# Prática 5 — MK-VFD7 com Python

> *"Quando o controle precisa ser automatizado e preciso, Python entrega."*

## 1. Contexto Industrial

Em uma planta real, raramente um operador fica enviando comandos manualmente para um inversor. As sequências de controle são **automatizadas** por:

- **CLPs** (controladores programáveis) executando lógica ladder
- **Scripts Python** rodando em servidores ou edge devices
- **Sistemas SCADA** que disparam macros

Casos típicos onde Python é usado para controlar inversores:

- **Rampas de partida customizadas** (ex.: bombas que precisam de ramp-up especial)
- **Sequências coordenadas** (ex.: ligar bomba 1 → esperar 10s → ligar bomba 2)
- **Receitas de processo** (parâmetros diferentes para produtos diferentes)
- **Manutenção preditiva** (monitorar temperatura/corrente e desligar antes de falha)
- **Test automation** (validação de inversores em produção/fábrica)

Nesta prática, você implementará uma série de sequências de controle do MK-VFD7 com **boa engenharia de software**: tratamento de erros, lógica de timeout, logging, encerramento gracioso.

---

## 2. Conceitos Necessários

### 2.1 Mapa de Registradores do MK-VFD7

**Medições (FC04):**

| Endereço | Variável         | Tipo    |
|----------|------------------|---------|
| 0–1      | Output Frequency | FLOAT32 |
| 4–5      | Output Current   | FLOAT32 |
| 8–9      | Motor Speed      | FLOAT32 |
| 26       | Drive Status     | UINT16  |
| 27       | Fault Code       | UINT16  |
| 28       | Warning Code     | UINT16  |

**Controle (FC03/FC06/FC16):**

| Endereço | Variável             | Tipo    |
|----------|----------------------|---------|
| 100      | Control Word         | UINT16  |
| 101–102  | Frequency Reference  | FLOAT32 |
| 103–104  | Acceleration Time    | FLOAT32 |

### 2.2 Control Word

| Valor | Ação           |
|-------|----------------|
| 0     | Stop           |
| 1     | Run forward    |
| 3     | Run reverse    |
| 5     | Jog forward    |

### 2.3 Drive Status Word (bits)

| Bit | Significado    |
|-----|----------------|
| 0   | Running        |
| 1   | Forward        |
| 2   | Reverse        |
| 3   | At reference   |
| 4   | Accelerating   |
| 5   | Decelerating   |
| 6   | Fault          |

---

## 3. Material Necessário

- 1 **smartphone Android** com **ModbusDeviceSIM** instalado, modo **REMOTE**
- 1 **laptop** com Python 3.10+ e pymodbus 3.x
- Conexão Wi-Fi compartilhada

---

## 4. Setup Inicial

### 4.1 No smartphone

1. Abra o app, selecione **MK-VFD7**, **START**.
2. **CRUCIAL:** coloque em modo **REMOTE** (switch no painel).
3. Anote o IP.

### 4.2 No laptop

```
mkdir pratica-vfd7-python
cd pratica-vfd7-python
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
pip install pymodbus
```

---

## 5. Procedimento

### Etapa 1 — Helper: Cliente VFD com API de Alto Nível

Crie `vfd_client.py` — uma classe que encapsula os comandos do drive:

```python
"""
Cliente Python para o MK-VFD7.
Fornece uma API de alto nível sobre pymodbus.
"""
from pymodbus.client import ModbusTcpClient
import struct
import time
from dataclasses import dataclass


@dataclass
class DriveStatus:
    running: bool
    forward: bool
    reverse: bool
    at_reference: bool
    accelerating: bool
    decelerating: bool
    fault: bool
    fault_code: int
    warning_code: int
    output_frequency: float
    output_current: float
    motor_speed: float


def words_to_float(h, l):
    return struct.unpack(">f", struct.pack(">HH", h, l))[0]


def float_to_words(value):
    return struct.unpack(">HH", struct.pack(">f", value))


class Vfd7Client:
    """Cliente para o MK-VFD7."""

    # Control Word bits
    BIT_RUN          = 0x0001
    BIT_REVERSE      = 0x0002
    BIT_JOG          = 0x0004
    BIT_FAULT_RESET  = 0x0008
    BIT_ESTOP        = 0x0010

    # Status Word bits
    STATUS_RUNNING       = 0x0001
    STATUS_FORWARD       = 0x0002
    STATUS_REVERSE       = 0x0004
    STATUS_AT_REFERENCE  = 0x0008
    STATUS_ACCELERATING  = 0x0010
    STATUS_DECELERATING  = 0x0020
    STATUS_FAULT         = 0x0040

    def __init__(self, host, port=5020, unit_id=1):
        self.client = ModbusTcpClient(host, port=port, timeout=3.0)
        self.unit_id = unit_id

    def connect(self):
        return self.client.connect()

    def close(self):
        self.client.close()

    def set_frequency_reference(self, hz: float):
        """Define a frequência de referência (Hz)."""
        hi, lo = float_to_words(hz)
        r = self.client.write_registers(address=101, values=[hi, lo], device_id=self.unit_id)
        return not r.isError()

    def set_acceleration_time(self, seconds: float):
        """Define o tempo de aceleração (s)."""
        hi, lo = float_to_words(seconds)
        r = self.client.write_registers(address=103, values=[hi, lo], device_id=self.unit_id)
        return not r.isError()

    def set_control_word(self, value: int):
        """Define a Control Word completa."""
        r = self.client.write_register(address=100, value=value, device_id=self.unit_id)
        return not r.isError()

    def run_forward(self):
        return self.set_control_word(self.BIT_RUN)

    def run_reverse(self):
        return self.set_control_word(self.BIT_RUN | self.BIT_REVERSE)

    def stop(self):
        return self.set_control_word(0)

    def fault_reset(self):
        """Pulso de fault reset (bit 3)."""
        self.set_control_word(self.BIT_FAULT_RESET)
        time.sleep(0.1)
        return self.set_control_word(0)

    def get_status(self) -> DriveStatus:
        """Lê o estado completo do drive."""
        r = self.client.read_input_registers(address=0, count=29, device_id=self.unit_id)
        if r.isError():
            raise IOError(f"Modbus read error: {r}")

        regs = r.registers
        status = regs[26]
        return DriveStatus(
            running       = bool(status & self.STATUS_RUNNING),
            forward       = bool(status & self.STATUS_FORWARD),
            reverse       = bool(status & self.STATUS_REVERSE),
            at_reference  = bool(status & self.STATUS_AT_REFERENCE),
            accelerating  = bool(status & self.STATUS_ACCELERATING),
            decelerating  = bool(status & self.STATUS_DECELERATING),
            fault         = bool(status & self.STATUS_FAULT),
            fault_code    = regs[27],
            warning_code  = regs[28],
            output_frequency = words_to_float(regs[0], regs[1]),
            output_current   = words_to_float(regs[4], regs[5]),
            motor_speed      = words_to_float(regs[8], regs[9]),
        )
```

> 💡 Esse arquivo encapsula a complexidade Modbus em uma API limpa. Você usará `vfd.run_forward()` em vez de `client.write_register(100, 1, device_id=1)`. **Isso é boa engenharia de software.**

---

### Etapa 2 — Teste Básico

Crie `01_test_basic.py`:

```python
"""
Prática 5 — Etapa 2: teste básico da classe Vfd7Client.
"""
from vfd_client import Vfd7Client
import time

HOST = "192.168.0.107"
PORT = 5020

vfd = Vfd7Client(HOST, port=PORT)
if not vfd.connect():
    print("❌ Falha de conexão")
    exit(1)

print(f"✓ Conectado em {HOST}:{PORT}\n")

# Configura referência
print("Definindo frequência de referência = 30 Hz...")
vfd.set_frequency_reference(30.0)
time.sleep(0.5)

# Lê status inicial
status = vfd.get_status()
print(f"Estado inicial: running={status.running}, freq={status.output_frequency:.2f} Hz")

vfd.close()
```

Execute. Saída esperada:

```
✓ Conectado em 192.168.0.107:5020

Definindo frequência de referência = 30 Hz...
Estado inicial: running=False, freq=0.00 Hz
```

---

### Etapa 3 — Sequência de Partida Monitorada

Crie `02_start_monitored.py`:

```python
"""
Prática 5 — Etapa 3: partida com monitoração da rampa.
"""
from vfd_client import Vfd7Client
import time

HOST = "192.168.0.107"
SETPOINT = 40.0   # Hz
TIMEOUT = 30      # segundos


def wait_for_reference(vfd, setpoint, tolerance=0.5, timeout=30):
    """Espera o drive atingir a referência (com timeout)."""
    print(f"Aguardando frequência atingir {setpoint} Hz...")
    start = time.time()
    while time.time() - start < timeout:
        s = vfd.get_status()
        elapsed = time.time() - start
        print(f"  t={elapsed:5.1f}s  f={s.output_frequency:6.2f} Hz  "
              f"speed={s.motor_speed:7.1f} RPM  current={s.output_current:5.2f}A  "
              f"{'ACC' if s.accelerating else '   '} "
              f"{'AT_REF' if s.at_reference else '      '}")
        if abs(s.output_frequency - setpoint) < tolerance:
            print(f"\n✓ Referência atingida em {elapsed:.1f}s")
            return True
        if s.fault:
            print(f"\n❌ Falha durante rampa: fault_code = {s.fault_code}")
            return False
        time.sleep(1.0)
    print(f"\n⚠ Timeout após {timeout}s")
    return False


def main():
    vfd = Vfd7Client(HOST)
    vfd.connect()

    try:
        # Configura
        vfd.set_frequency_reference(SETPOINT)
        time.sleep(0.5)

        # Parte
        print(f"\n>>> Iniciando drive em {SETPOINT} Hz forward\n")
        vfd.run_forward()

        # Monitora rampa
        wait_for_reference(vfd, SETPOINT, timeout=TIMEOUT)

        # Roda em referência por alguns segundos
        print("\nMantendo em referência por 5 segundos...")
        time.sleep(5)

        # Para
        print("\n>>> Comando STOP")
        vfd.stop()

        # Monitora desaceleração
        while True:
            s = vfd.get_status()
            print(f"  f={s.output_frequency:5.2f} Hz  {'DEC' if s.decelerating else 'STOP'}")
            if s.output_frequency < 0.5:
                break
            time.sleep(1)

        print("\n✓ Sequência concluída")
    finally:
        vfd.stop()  # garantia em caso de exceção
        vfd.close()


if __name__ == "__main__":
    main()
```

Execute. Observe:

- A rampa de aceleração (frequência subindo)
- Os flags ACC e AT_REF mudando conforme o estado
- A rampa de desaceleração ao receber STOP

**No smartphone**, acompanhe visualmente no LCD do app.

---

### Etapa 4 — Receita: Soft-start com Múltiplos Setpoints

Em algumas aplicações (ex.: bombas centrífugas em sistemas com inércia), é desejável uma partida **escalonada** — passar por velocidades intermediárias para reduzir picos de corrente.

Crie `03_softstart.py`:

```python
"""
Prática 5 — Etapa 4: soft-start escalonado.
"""
from vfd_client import Vfd7Client
import time

HOST = "192.168.0.107"

# Sequência: (frequência alvo, tempo de permanência)
RECIPE = [
    (10.0,  5),
    (20.0,  5),
    (35.0,  5),
    (50.0, 10),
]


def main():
    vfd = Vfd7Client(HOST)
    vfd.connect()

    try:
        # Acceleration time mais rápido para essa receita
        vfd.set_acceleration_time(3.0)
        time.sleep(0.5)

        # Inicia em primeira velocidade
        first_freq, _ = RECIPE[0]
        vfd.set_frequency_reference(first_freq)
        time.sleep(0.3)
        vfd.run_forward()
        print(f">>> Soft-start iniciado, alvo inicial: {first_freq} Hz")

        for i, (freq, duration) in enumerate(RECIPE, start=1):
            print(f"\nEtapa {i}/{len(RECIPE)}: {freq} Hz por {duration}s")
            vfd.set_frequency_reference(freq)

            # Espera atingir referência
            while True:
                s = vfd.get_status()
                if abs(s.output_frequency - freq) < 0.5:
                    print(f"  ✓ atingiu {freq} Hz")
                    break
                if s.fault:
                    print(f"  ❌ Falha! fault_code={s.fault_code}")
                    return
                print(f"  ... f={s.output_frequency:.2f} Hz")
                time.sleep(0.5)

            # Permanece em velocidade
            for sec in range(duration):
                s = vfd.get_status()
                print(f"  [permanecer] t={sec+1}/{duration}  f={s.output_frequency:.2f}Hz  "
                      f"I={s.output_current:.2f}A")
                time.sleep(1)

        # Stop final
        print("\n>>> STOP final")
        vfd.stop()

        # Aguarda desaceleração
        while True:
            s = vfd.get_status()
            if s.output_frequency < 0.5:
                break
            time.sleep(0.5)

        print("\n✓ Soft-start concluído com sucesso")
    finally:
        vfd.stop()
        vfd.close()


if __name__ == "__main__":
    main()
```

Execute. Esta é uma **receita típica de processo industrial** — sequências programadas de comandos com monitoração ativa.

---

### Etapa 5 — Detecção e Recuperação de Falha

Crie `04_fault_handling.py`:

```python
"""
Prática 5 — Etapa 5: detecção e recuperação automática de falha.
"""
from vfd_client import Vfd7Client
import time

HOST = "192.168.0.107"


def run_with_fault_recovery(vfd, setpoint, max_retries=3):
    """Tenta rodar o drive; em caso de falha, faz reset e tenta de novo."""
    for attempt in range(1, max_retries + 1):
        print(f"\n[Tentativa {attempt}/{max_retries}]")
        vfd.set_frequency_reference(setpoint)
        vfd.run_forward()
        time.sleep(2)

        # Monitora por 10 segundos
        start = time.time()
        while time.time() - start < 10:
            s = vfd.get_status()
            if s.fault:
                print(f"  ❌ Falha detectada! Code: {s.fault_code}")
                vfd.stop()
                time.sleep(1)
                print(f"  Executando fault reset...")
                vfd.fault_reset()
                time.sleep(2)
                # Continua para nova tentativa
                break
            print(f"  ✓ rodando f={s.output_frequency:.2f}Hz")
            time.sleep(1)
        else:
            # Sem falha durante o monitoramento
            print(f"  ✓ Operação estável")
            return True

    print(f"\n❌ Não conseguiu operar após {max_retries} tentativas")
    return False


def main():
    vfd = Vfd7Client(HOST)
    vfd.connect()
    try:
        success = run_with_fault_recovery(vfd, setpoint=35.0)
        if success:
            print("\n>>> Operação concluída com sucesso")
            time.sleep(3)
        vfd.stop()
    finally:
        vfd.stop()
        vfd.close()


if __name__ == "__main__":
    main()
```

> **Provocando uma falha (para testar):** durante a operação, reduza no app (em modo LOCAL temporário, ou via outra ferramenta) o threshold de Over-Current para um valor abaixo da corrente atual. Isso deve disparar fault_code = 1.

---

### Etapa 6 — Logging de Operação

Crie `05_logger.py`:

```python
"""
Prática 5 — Etapa 6: log estruturado de operação do VFD.
"""
from vfd_client import Vfd7Client
from datetime import datetime
from pathlib import Path
import csv
import time
import signal

HOST = "192.168.0.107"
CSV_FILE = Path("vfd_log.csv")
POLL_INTERVAL = 1.0

stop_flag = False


def on_signal(sig, frame):
    global stop_flag
    stop_flag = True


def main():
    signal.signal(signal.SIGINT, on_signal)
    vfd = Vfd7Client(HOST)
    vfd.connect()

    fields = [
        "timestamp", "running", "forward", "reverse",
        "at_reference", "accelerating", "decelerating",
        "fault", "fault_code", "warning_code",
        "output_frequency", "output_current", "motor_speed",
    ]

    file_exists = CSV_FILE.exists()
    f = CSV_FILE.open("a", newline="")
    writer = csv.DictWriter(f, fieldnames=fields)
    if not file_exists:
        writer.writeheader()

    print(f"Logging em {CSV_FILE.resolve()}\nCtrl-C para parar.\n")

    count = 0
    while not stop_flag:
        try:
            s = vfd.get_status()
            row = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "running": s.running,
                "forward": s.forward,
                "reverse": s.reverse,
                "at_reference": s.at_reference,
                "accelerating": s.accelerating,
                "decelerating": s.decelerating,
                "fault": s.fault,
                "fault_code": s.fault_code,
                "warning_code": s.warning_code,
                "output_frequency": round(s.output_frequency, 2),
                "output_current": round(s.output_current, 2),
                "motor_speed": round(s.motor_speed, 1),
            }
            writer.writerow(row)
            f.flush()
            count += 1
            print(f"[{count:04d}] {row['timestamp']}  f={s.output_frequency:6.2f}Hz  "
                  f"I={s.output_current:5.2f}A  "
                  f"{'RUN' if s.running else 'STOP'}")
        except Exception as e:
            print(f"  [erro] {e}")
        time.sleep(POLL_INTERVAL)

    f.close()
    vfd.close()
    print(f"\n{count} registros salvos.")


if __name__ == "__main__":
    main()
```

**Enquanto o logger roda**, em **outra janela**, execute um dos scripts de comando (02 ou 03). O logger registrará toda a sequência. Bom para auditoria e análise pós-evento.

---

## 6. Critérios de Sucesso

Você completou esta prática se:

- ✅ Implementou a **classe `Vfd7Client`** com API de alto nível (Etapa 1).
- ✅ Executou uma **partida monitorada** mostrando rampa de aceleração (Etapa 3).
- ✅ Implementou um **soft-start escalonado** com pelo menos 4 etapas (Etapa 4).
- ✅ Implementou detecção e recuperação de falha (Etapa 5).
- ✅ Gerou um **arquivo CSV** com pelo menos 60 amostras incluindo eventos de start/stop (Etapa 6).

---

## 7. Discussão e Reflexão

1. **Engenharia de software.** Por que criamos a classe `Vfd7Client` em vez de espalhar chamadas Modbus por todo o código? Liste 3 vantagens dessa abstração.
2. **Reliability.** No `wait_for_reference()` há um **timeout** de 30s. O que aconteceria sem ele? Em quais situações o timeout protege contra deadlock?
3. **Análise.** Analisando o CSV gerado, calcule:
   - Tempo médio de aceleração (start até at_reference)
   - Pico de corrente durante aceleração
   - Tempo total que o drive ficou em fault (se aplicável)
4. **Coordenação.** Se você tivesse 5 inversores controlando 5 bombas em uma estação de tratamento de água, como organizaria o código Python? Discuta arquitetura.
5. **Reflexão.** Como você adaptaria esses scripts para um **CLP real** em vez de Python? Em quais partes da automação o Python complementa o CLP em vez de substituí-lo?

---

## 8. Entregáveis para Avaliação

Submeta:

1. **Os 5 arquivos Python** (com comentários).
2. **Capturas do terminal** de cada script em execução.
3. **Arquivo CSV** (`vfd_log.csv`) com pelo menos 60 amostras cobrindo eventos de start/stop.
4. **Gráfico** (matplotlib/Excel) mostrando frequency × time durante a execução do `03_softstart.py`.
5. **Respostas** às 5 perguntas da seção 7.

---

## 9. Solução de Problemas Específicos

| Sintoma | Causa | Solução |
|---------|-------|---------|
| Drive não responde | Modo LOCAL | Mude para REMOTE no app |
| `IOError: Modbus read error` | Conexão caiu | Reconecte; adicione retry no código |
| Drive inicia mas para imediatamente | Faltam pré-condições | Verifique fault_code |
| Frequência fica em 0 mesmo com RUN | Frequency Reference = 0 | `vfd.set_frequency_reference(30.0)` antes |
| Script trava esperando referência | Setpoint maior que Max Freq | Verifique reg 107-108 |
| Logger não cria arquivo | Permissão de pasta | Rode em pasta com permissão de escrita |

---

## 10. Próximos Passos

- **[Prática 6 — VFD7 com Node-RED](16-pratica-vfd7-nodered.md)**: traga o mesmo controle para um dashboard visual.
- **[Prática Grupo 2 — 1 cliente / 3 VFDs](18-pratica-grupo-2-1cliente-3vfds.md)**: coordene múltiplos inversores.

---

**Boa programação!**
