# Prática 2 — MK-EM3P com Python

> *"Quando você precisa coletar dados de forma automatizada, persistente e robusta — Python é seu aliado."*

## 1. Contexto Industrial

Em uma planta industrial real, ninguém fica parado em frente a um EasyModbusTCP o dia inteiro. Os dados precisam ser **coletados automaticamente**, **registrados em histórico** e **disponibilizados para sistemas superiores** (SCADA, ERP, dashboards web).

A linguagem **Python** é hoje uma das ferramentas mais utilizadas para integração industrial, especialmente para:

- **Coleta de dados** (data acquisition) de medidores e sensores.
- **Cálculos derivados** (média móvel, consumo acumulado, KPIs).
- **Persistência** em arquivos, bancos de dados ou nuvem.
- **Alarmes** baseados em condições programáticas.
- **Integração** com APIs (REST, MQTT, OPC UA).

A biblioteca **pymodbus** é a referência aberta para Modbus em Python.

Nesta prática, você irá implementar:

1. Um cliente básico que lê algumas medições.
2. Um polling contínuo com tratamento de erros.
3. Cálculos derivados e logging em CSV.
4. Escrita de configuração de forma segura.

---

## 2. Conceitos Necessários

### 2.1 Python e ambiente virtual

Vamos usar Python 3.10+ com **pymodbus 3.x** (a versão mais recente).

### 2.2 Decodificação FLOAT32 em Python

Python tem o módulo **struct** para empacotamento/desempacotamento de bytes:

```python
import struct

def words_to_float(high: int, low: int) -> float:
    """Combina 2 registradores Modbus (ABCD) em um IEEE 754 float."""
    packed = struct.pack(">HH", high, low)  # H = uint16 big-endian
    return struct.unpack(">f", packed)[0]   # f = float big-endian

def float_to_words(value: float) -> tuple[int, int]:
    """Converte float para 2 registradores (ABCD)."""
    packed = struct.pack(">f", value)
    return struct.unpack(">HH", packed)
```

### 2.3 Mapa de registradores do MK-EM3P (relembrado)

| Endereço | Variável         | Tipo    | Unidade |
|----------|------------------|---------|---------|
| 0–1      | Voltage L1-N     | FLOAT32 | V       |
| 2–3      | Voltage L2-N     | FLOAT32 | V       |
| 4–5      | Voltage L3-N     | FLOAT32 | V       |
| 12–13    | Current L1       | FLOAT32 | A       |
| 14–15    | Current L2       | FLOAT32 | A       |
| 16–17    | Current L3       | FLOAT32 | A       |
| 26–27    | Active Power Total | FLOAT32 | kW    |
| 50–51    | Power Factor Total | FLOAT32 | —     |
| 52–53    | Frequency        | FLOAT32 | Hz      |
| 54–55    | Active Energy    | UINT32  | kWh     |
| 90       | Alarm Status     | UINT16  | bitmask |
| 100      | CT Primary       | UINT16  | A       |
| 107–108  | Over-Voltage Threshold | FLOAT32 | V |

---

## 3. Material Necessário

- 1 **smartphone Android** com **ModbusDeviceSIM** instalado
- 1 **laptop** com:
  - Python **3.10 ou superior**
  - **pip** funcional
  - Editor de código (VS Code, PyCharm, ou qualquer um)
- Conexão Wi-Fi compartilhada

---

## 4. Setup Inicial

### 4.1 No smartphone

1. Abra o **ModbusDeviceSIM**.
2. Selecione **MK-EM3P**.
3. Toque em **START**.
4. Anote o IP exibido (ex.: `192.168.0.105:5020`).

### 4.2 No laptop

**Crie uma pasta** para esta prática:

```
mkdir pratica-em3p-python
cd pratica-em3p-python
```

**Crie um ambiente virtual** (recomendado):

```
python -m venv venv
```

**Ative o ambiente:**

- Windows (PowerShell):
  ```
  .\venv\Scripts\Activate.ps1
  ```
- Windows (cmd):
  ```
  venv\Scripts\activate.bat
  ```
- Linux/macOS:
  ```
  source venv/bin/activate
  ```

**Instale o pymodbus:**

```
pip install pymodbus
```

---

## 5. Procedimento

### Etapa 1 — Hello, Modbus!

Crie o arquivo `01_hello_modbus.py`:

```python
"""
Prática 2 — Etapa 1: Conexão básica e leitura de um valor.
"""
from pymodbus.client import ModbusTcpClient
import struct

# === Configurações — ajuste para o IP do seu smartphone ===
HOST = "192.168.0.105"
PORT = 5020
UNIT = 1


def words_to_float(high: int, low: int) -> float:
    """Decodifica FLOAT32 ABCD a partir de 2 registradores."""
    return struct.unpack(">f", struct.pack(">HH", high, low))[0]


def main():
    client = ModbusTcpClient(HOST, port=PORT)
    if not client.connect():
        print(f"❌ Falha ao conectar em {HOST}:{PORT}")
        return

    print(f"✓ Conectado em {HOST}:{PORT}")

    # Ler Voltage L1-N (registradores 0-1, FC04)
    result = client.read_input_registers(address=0, count=2, device_id=UNIT)

    if result.isError():
        print(f"❌ Erro de leitura: {result}")
    else:
        voltage = words_to_float(result.registers[0], result.registers[1])
        print(f"  Voltage L1-N: {voltage:.2f} V")

    client.close()


if __name__ == "__main__":
    main()
```

Execute:

```
python 01_hello_modbus.py
```

Saída esperada:

```
✓ Conectado em 192.168.0.105:5020
  Voltage L1-N: 224.32 V
```

**Verifique no smartphone:** o contador **Clients** sobe brevemente para 1 e depois cai para 0 (o script desconecta ao final).

---

### Etapa 2 — Leitura Completa das Medições

Crie `02_full_read.py`:

```python
"""
Prática 2 — Etapa 2: Lê várias medições e exibe formatadas.
"""
from pymodbus.client import ModbusTcpClient
import struct

HOST = "192.168.0.105"
PORT = 5020
UNIT = 1


def words_to_float(high, low):
    return struct.unpack(">f", struct.pack(">HH", high, low))[0]


def words_to_uint32(high, low):
    return (high << 16) | low


# Lista de medições: (endereço, nome, tipo, unidade)
MEASUREMENTS = [
    (0,  "Voltage L1-N",   "float", "V"),
    (2,  "Voltage L2-N",   "float", "V"),
    (4,  "Voltage L3-N",   "float", "V"),
    (12, "Current L1",     "float", "A"),
    (14, "Current L2",     "float", "A"),
    (16, "Current L3",     "float", "A"),
    (26, "Active Power",   "float", "kW"),
    (50, "Power Factor",   "float", ""),
    (52, "Frequency",      "float", "Hz"),
    (54, "Active Energy",  "uint32", "kWh"),
]


def read_block(client, start, count):
    """Lê um bloco contíguo de input registers."""
    r = client.read_input_registers(address=start, count=count, device_id=UNIT)
    if r.isError():
        return None
    return r.registers


def main():
    client = ModbusTcpClient(HOST, port=PORT)
    client.connect()

    # Lê um bloco grande de uma vez (mais eficiente que múltiplas leituras)
    regs = read_block(client, 0, 92)
    if not regs:
        print("❌ Falha na leitura")
        return

    print(f"\n{'─' * 60}")
    print(f"  MK-EM3P — Leitura em {HOST}")
    print(f"{'─' * 60}")

    for addr, name, dtype, unit in MEASUREMENTS:
        if dtype == "float":
            value = words_to_float(regs[addr], regs[addr + 1])
            print(f"  {name:18}: {value:10.2f} {unit}")
        elif dtype == "uint32":
            value = words_to_uint32(regs[addr], regs[addr + 1])
            print(f"  {name:18}: {value:10d} {unit}")

    client.close()


if __name__ == "__main__":
    main()
```

Execute. Saída esperada:

```
────────────────────────────────────────────────────────────
  MK-EM3P — Leitura em 192.168.0.105
────────────────────────────────────────────────────────────
  Voltage L1-N      :     224.32 V
  Voltage L2-N      :     220.18 V
  Voltage L3-N      :     219.74 V
  Current L1        :      15.04 A
  ...
```

---

### Etapa 3 — Polling Contínuo com Tratamento de Erros

Crie `03_polling.py`:

```python
"""
Prática 2 — Etapa 3: Polling contínuo com reconexão automática.
"""
from pymodbus.client import ModbusTcpClient
import struct
import time
import signal
import sys

HOST = "192.168.0.105"
PORT = 5020
UNIT = 1
POLL_INTERVAL = 2.0  # segundos


def words_to_float(h, l):
    return struct.unpack(">f", struct.pack(">HH", h, l))[0]


PARAMS = [
    (0,  "V L1",  "V"),
    (2,  "V L2",  "V"),
    (4,  "V L3",  "V"),
    (26, "P Tot", "kW"),
    (52, "Freq",  "Hz"),
]

stop_flag = False


def on_signal(sig, frame):
    global stop_flag
    print("\n[Sinal recebido] encerrando...")
    stop_flag = True


def connect_with_retry(host, port, max_retries=3):
    """Tenta conectar com retry."""
    client = ModbusTcpClient(host, port=port, timeout=2.0)
    for attempt in range(1, max_retries + 1):
        if client.connect():
            print(f"✓ Conectado (tentativa {attempt})")
            return client
        print(f"  ... tentativa {attempt} falhou")
        time.sleep(1)
    return None


def main():
    signal.signal(signal.SIGINT, on_signal)
    client = connect_with_retry(HOST, PORT)
    if not client:
        print(f"❌ Não conseguiu conectar em {HOST}:{PORT}")
        return

    print(f"\nPolling a cada {POLL_INTERVAL}s. Ctrl-C para parar.\n")

    error_count = 0
    poll_count = 0

    while not stop_flag:
        try:
            r = client.read_input_registers(address=0, count=92, device_id=UNIT)
            if r.isError():
                error_count += 1
                print(f"  [erro {error_count}] {r}")
            else:
                poll_count += 1
                line = f"#{poll_count:04d}  "
                for addr, name, unit in PARAMS:
                    v = words_to_float(r.registers[addr], r.registers[addr + 1])
                    line += f"{name}={v:6.2f}{unit}  "
                print(line)
        except Exception as e:
            error_count += 1
            print(f"  [exceção] {e}")
            # Tenta reconectar
            client.close()
            time.sleep(2)
            client = connect_with_retry(HOST, PORT)
            if not client:
                print("Reconexão falhou. Encerrando.")
                break

        time.sleep(POLL_INTERVAL)

    if client:
        client.close()
    print(f"\nTotal: {poll_count} leituras OK, {error_count} erros")


if __name__ == "__main__":
    main()
```

Execute:

```
python 03_polling.py
```

Deixe rodar por **30 segundos** e pressione **Ctrl-C** para parar.

**Teste a reconexão:** durante a execução, **toque STOP** no smartphone. O script detecta o erro e tenta reconectar. Toque **START** novamente; o script deve voltar a funcionar.

---

### Etapa 4 — Cálculos Derivados e Logging CSV

Crie `04_logger.py`:

```python
"""
Prática 2 — Etapa 4: Coleta com cálculos e log em CSV.
"""
from pymodbus.client import ModbusTcpClient
import struct
import time
import csv
import signal
from datetime import datetime
from pathlib import Path

HOST = "192.168.0.105"
PORT = 5020
UNIT = 1
POLL_INTERVAL = 5.0
CSV_FILE = Path("em3p_log.csv")

stop_flag = False


def on_signal(sig, frame):
    global stop_flag
    stop_flag = True


def words_to_float(h, l):
    return struct.unpack(">f", struct.pack(">HH", h, l))[0]


def read_em3p(client):
    """Lê todas as variáveis relevantes e retorna como dict."""
    r = client.read_input_registers(address=0, count=92, device_id=UNIT)
    if r.isError():
        return None

    regs = r.registers
    data = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "v_l1": words_to_float(regs[0], regs[1]),
        "v_l2": words_to_float(regs[2], regs[3]),
        "v_l3": words_to_float(regs[4], regs[5]),
        "i_l1": words_to_float(regs[12], regs[13]),
        "i_l2": words_to_float(regs[14], regs[15]),
        "i_l3": words_to_float(regs[16], regs[17]),
        "p_total": words_to_float(regs[26], regs[27]),
        "pf_total": words_to_float(regs[50], regs[51]),
        "frequency": words_to_float(regs[52], regs[53]),
        "alarm_status": regs[90],
    }

    # Cálculos derivados
    data["v_avg"] = (data["v_l1"] + data["v_l2"] + data["v_l3"]) / 3
    data["i_avg"] = (data["i_l1"] + data["i_l2"] + data["i_l3"]) / 3
    data["unbalance_v"] = max(abs(data["v_l1"] - data["v_avg"]),
                               abs(data["v_l2"] - data["v_avg"]),
                               abs(data["v_l3"] - data["v_avg"])) / data["v_avg"] * 100
    data["alarm_over_voltage"] = bool(data["alarm_status"] & 0x0001)
    data["alarm_under_voltage"] = bool(data["alarm_status"] & 0x0002)
    data["alarm_over_current"] = bool(data["alarm_status"] & 0x0004)

    return data


def main():
    signal.signal(signal.SIGINT, on_signal)
    client = ModbusTcpClient(HOST, port=PORT)
    client.connect()

    # Cria arquivo CSV com header se ainda não existe
    fields = [
        "timestamp", "v_l1", "v_l2", "v_l3", "v_avg",
        "i_l1", "i_l2", "i_l3", "i_avg",
        "p_total", "pf_total", "frequency",
        "unbalance_v",
        "alarm_status", "alarm_over_voltage", "alarm_under_voltage", "alarm_over_current",
    ]

    file_exists = CSV_FILE.exists()
    f = CSV_FILE.open("a", newline="")
    writer = csv.DictWriter(f, fieldnames=fields)
    if not file_exists:
        writer.writeheader()

    print(f"Logging em {CSV_FILE.resolve()}")
    print(f"Polling a cada {POLL_INTERVAL}s. Ctrl-C para parar.\n")

    count = 0
    while not stop_flag:
        data = read_em3p(client)
        if data:
            writer.writerow(data)
            f.flush()
            count += 1
            alarms = []
            if data["alarm_over_voltage"]:  alarms.append("OV")
            if data["alarm_under_voltage"]: alarms.append("UV")
            if data["alarm_over_current"]:  alarms.append("OC")
            alarm_str = ", ".join(alarms) if alarms else "OK"
            print(f"  [{count:04d}] V_avg={data['v_avg']:6.2f}V  "
                  f"P={data['p_total']:5.2f}kW  "
                  f"Unb={data['unbalance_v']:.2f}%  "
                  f"Status={alarm_str}")
        else:
            print("  [erro] leitura falhou")

        time.sleep(POLL_INTERVAL)

    f.close()
    client.close()
    print(f"\n{count} registros salvos em {CSV_FILE}")


if __name__ == "__main__":
    main()
```

Execute por **2 a 3 minutos**. Você verá um log:

```
  [0001] V_avg=221.41V  P= 9.85kW  Unb=0.71%  Status=OK
  [0002] V_avg=221.83V  P= 9.79kW  Unb=0.65%  Status=OK
  ...
```

**Verifique o arquivo CSV gerado.** Abra com Excel ou um editor de texto.

---

### Etapa 5 — Escrita de Configuração Segura

Crie `05_safe_write.py`:

```python
"""
Prática 2 — Etapa 5: Escreve configuração com verificação.
"""
from pymodbus.client import ModbusTcpClient
import struct

HOST = "192.168.0.105"
PORT = 5020
UNIT = 1


def words_to_float(h, l):
    return struct.unpack(">f", struct.pack(">HH", h, l))[0]


def float_to_words(value):
    return struct.unpack(">HH", struct.pack(">f", value))


def safe_write_float(client, address, value):
    """
    Escreve um FLOAT32 e verifica leitura de volta.
    Retorna True se sucesso, False caso contrário.
    """
    hi, lo = float_to_words(value)
    write_result = client.write_registers(address=address, values=[hi, lo], device_id=UNIT)
    if write_result.isError():
        print(f"  ❌ Escrita falhou: {write_result}")
        return False

    # Verifica
    read_result = client.read_holding_registers(address=address, count=2, device_id=UNIT)
    if read_result.isError():
        print(f"  ❌ Leitura de verificação falhou: {read_result}")
        return False

    actual = words_to_float(read_result.registers[0], read_result.registers[1])
    if abs(actual - value) < 0.01:
        print(f"  ✓ Escrita confirmada: {actual:.2f}")
        return True
    else:
        print(f"  ❌ Valor lido ({actual:.2f}) difere do escrito ({value:.2f})")
        return False


def main():
    client = ModbusTcpClient(HOST, port=PORT)
    client.connect()

    # Lê valor atual
    r = client.read_holding_registers(address=107, count=2, device_id=UNIT)
    current = words_to_float(r.registers[0], r.registers[1])
    print(f"Over-Voltage Threshold atual: {current:.2f} V")

    # Define novo valor
    new_value = 250.0
    print(f"\nDefinindo novo threshold: {new_value:.2f} V")
    if safe_write_float(client, 107, new_value):
        print("\n✓ Configuração aplicada com sucesso")
    else:
        print("\n❌ Falha na configuração")

    # Restaura
    print(f"\nRestaurando para {current:.2f} V")
    safe_write_float(client, 107, current)

    client.close()


if __name__ == "__main__":
    main()
```

Execute. A função `safe_write_float` **escreve e verifica** — uma boa prática para garantir que comandos críticos foram aceitos pelo dispositivo.

---

## 6. Critérios de Sucesso

Você completou esta prática se conseguiu:

- ✅ Conectar via Python e ler ao menos uma medição corretamente (Etapa 1).
- ✅ Implementar a função `words_to_float` e produzir uma tabela com todas as medições (Etapa 2).
- ✅ Executar polling contínuo com **detecção de erro e reconexão** (Etapa 3).
- ✅ Gerar um arquivo CSV com pelo menos **20 amostras**, incluindo cálculos derivados (Etapa 4).
- ✅ Escrever um FLOAT32 com **verificação de leitura** (Etapa 5).

---

## 7. Discussão e Reflexão

1. **Performance.** Compare o tempo total para ler:
   - 5 leituras separadas (Voltage L1, Voltage L2, Voltage L3, Power, Frequency), cada uma com 2 registradores.
   - 1 leitura única de 54 registradores.
   Use `time.time()` antes e depois. Qual é mais rápido? Por quê?
2. **Robustez.** Que outras condições de erro o script de polling (Etapa 3) **não** trata? Liste 3.
3. **Cálculo.** O desbalanço de tensão (unbalance) é uma medida importante em sistemas trifásicos. Por que ele é calculado da forma mostrada na Etapa 4? Qual seria o limite recomendado para um sistema saudável?
4. **Boas práticas.** Por que a função `safe_write_float` da Etapa 5 **lê de volta** após escrever? Em quais situações industriais isso é crítico?
5. **Discussão.** Comparado com EasyModbusTCP (Prática 1), em quais situações você usaria Python? E em quais situações continuaria usando uma ferramenta gráfica?

---

## 8. Entregáveis para Avaliação

Submeta:

1. **Os 5 scripts** (`01_hello_modbus.py` a `05_safe_write.py`) **com comentários** explicando trechos não-óbvios.
2. **Captura do terminal** mostrando saída de cada script.
3. **Arquivo CSV** com **pelo menos 20 registros** coletados.
4. **Análise dos dados do CSV**: gere um gráfico (use Excel, ou matplotlib) mostrando a tensão L1 ao longo do tempo.
5. **Respostas** às 5 perguntas da seção 7.

---

## 9. Solução de Problemas Específicos

| Sintoma | Causa | Solução |
|---------|-------|---------|
| `ModuleNotFoundError: pymodbus` | Não instalou ou venv não ativo | `pip install pymodbus` no venv |
| `ConnectionRefusedError` | App não está RUNNING | Pressione START no smartphone |
| `TypeError: read_input_registers() got unexpected keyword 'slave'` | pymodbus 2.x antiga | Atualize: `pip install -U pymodbus` |
| `result.isError()` retorna True | Endereço inválido ou FC errada | Confira o mapa de registradores |
| Valores aleatórios em FLOAT32 | Ordem de bytes incorreta | Use `>HH` e `>f` (big-endian) |
| Script trava sem resposta | Timeout muito alto | Adicione `timeout=2.0` ao cliente |

---

## 10. Próximos Passos

- **[Prática 3 — EM3P com Node-RED](13-pratica-em3p-nodered.md)**: visualize os dados em um dashboard.
- **[Prática 5 — VFD7 com Python](15-pratica-vfd7-python.md)**: aplique os mesmos princípios ao inversor.

---

**Boa programação!**
