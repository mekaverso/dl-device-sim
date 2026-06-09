# Prática Grupo 2 — 1 Cliente Orquestrando 3 VFDs

> *"Quando uma única lógica precisa governar múltiplos motores, surge a orquestração — o coração de qualquer linha de produção."*

## 1. Contexto Industrial

Em muitos sistemas industriais, **um único controlador** coordena **múltiplos inversores** de forma sincronizada:

- **Esteiras transportadoras em série** — 3 motores devem ligar em sequência para evitar acúmulo
- **Bombas redundantes** — 2 bombas alternam serviço; uma 3ª assume se a demanda crescer
- **Sistemas de ventilação industrial** — múltiplos ventiladores ajustam vazão conjunta
- **Linhas de embalagem** — motor de tração, motor de etiquetagem, motor de empilhamento

Em todos esses casos, o **mesmo cérebro** (um CLP, um servidor edge, um script Python) toma decisões e envia comandos a **N inversores**. O cliente Modbus abre conexões TCP independentes para cada VFD e mantém comunicação contínua com todos.

Nesta prática, **a equipe colaborará** para implementar essa arquitetura: **3 smartphones simulando 3 VFDs** e **1 cliente (Python + Node-RED) orquestrando os três**.

---

## 2. Distribuição de Papéis

Embora apenas **1 cliente** orquestre, a equipe de **3 alunos** se organiza assim:

| Aluno | Função | Smartphone |
|-------|--------|-----------|
| **A** | **Orquestrador** — operador do laptop ativo (control client) | — |
| **B** | **Mantenedor do VFD-1** — garante que seu smartphone simule VFD-1 corretamente | Smartphone com MK-VFD7 (VFD-1) |
| **C** | **Mantenedor do VFD-2** — garante que seu smartphone simule VFD-2 corretamente | Smartphone com MK-VFD7 (VFD-2) |

O **terceiro smartphone** (VFD-3) é fornecido por qualquer um dos alunos.

**Rotação:** após as Etapas 1–4, os alunos **rotacionam o papel de Orquestrador** (B vira A, C vira B, etc.) para que todos pratiquem do lado do controle.

> O Orquestrador trabalha **no seu próprio laptop**, sentado no centro. Os outros 2 alunos cuidam dos smartphones, observam a operação e contribuem na discussão.

---

## 3. Material Necessário

- **3 smartphones Android** com ModbusDeviceSIM
- **3 laptops** (cada aluno tem seu próprio), com:
  - **Python 3.10+** com pymodbus 3.x
  - **Node-RED** com pacotes `node-red-contrib-modbus` e `node-red-dashboard`
- Wi-Fi comum a todos

---

## 4. Setup

### 4.1 Os 3 smartphones (cada um simula um VFD)

Cada smartphone faz:

1. Abrir ModbusDeviceSIM, selecionar **MK-VFD7**, **START**.
2. **Modo REMOTE**.
3. Anotar o IP.

A equipe registra:

```
   VFD-1: IP = 192.168.1.51:5020
   VFD-2: IP = 192.168.1.52:5020
   VFD-3: IP = 192.168.1.53:5020
```

### 4.2 No laptop do Orquestrador

```
mkdir orquestrador
cd orquestrador
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install pymodbus
```

### 4.3 Verificação

O Orquestrador testa do seu laptop:

```
ping 192.168.1.51
ping 192.168.1.52
ping 192.168.1.53
```

Todos devem responder.

---

## 5. Conceitos Necessários

### 5.1 Cliente Multi-conexão

Em Python, mantemos **3 instâncias separadas** de `ModbusTcpClient`, uma para cada VFD:

```python
clients = {
    "VFD1": ModbusTcpClient("192.168.1.51", port=5020),
    "VFD2": ModbusTcpClient("192.168.1.52", port=5020),
    "VFD3": ModbusTcpClient("192.168.1.53", port=5020),
}
for c in clients.values():
    c.connect()
```

Cada cliente abre uma conexão TCP independente. Lê-se e escreve-se em cada um separadamente.

### 5.2 Registradores essenciais do MK-VFD7

| Endereço | Variável             | Tipo    |
|----------|----------------------|---------|
| 0–1      | Output Frequency     | FLOAT32 |
| 4–5      | Output Current       | FLOAT32 |
| 8–9      | Motor Speed          | FLOAT32 |
| 26       | Drive Status (bits)  | UINT16  |
| 100      | Control Word         | UINT16  |
| 101–102  | Frequency Reference  | FLOAT32 |

### 5.3 Conversões

```python
import struct
def f32_to_words(v):
    return struct.unpack(">HH", struct.pack(">f", v))
def words_to_f32(h, l):
    return struct.unpack(">f", struct.pack(">HH", h, l))[0]
```

---

## 6. Procedimento

### Etapa 1 — Helper de Cliente Multi-VFD em Python (30 min)

Crie `multi_vfd.py`:

```python
"""
Helper para orquestrar múltiplos MK-VFD7.
"""
from pymodbus.client import ModbusTcpClient
from dataclasses import dataclass
import struct
import time


def words_to_float(h, l):
    return struct.unpack(">f", struct.pack(">HH", h, l))[0]


def float_to_words(v):
    return struct.unpack(">HH", struct.pack(">f", v))


@dataclass
class VfdState:
    frequency: float
    current: float
    speed: float
    running: bool
    forward: bool
    reverse: bool
    at_reference: bool
    fault: bool
    fault_code: int


class MultiVfd:
    """Orquestra múltiplos VFDs."""

    def __init__(self, vfd_map: dict[str, tuple[str, int]]):
        """vfd_map: {"VFD1": (host, port), ...}"""
        self.clients = {
            name: ModbusTcpClient(host, port=port, timeout=2.0)
            for name, (host, port) in vfd_map.items()
        }

    def connect_all(self):
        return {name: c.connect() for name, c in self.clients.items()}

    def close_all(self):
        for c in self.clients.values():
            c.close()

    def read_state(self, name: str) -> VfdState | None:
        c = self.clients[name]
        r = c.read_input_registers(address=0, count=29, device_id=1)
        if r.isError():
            return None
        regs = r.registers
        s = regs[26]
        return VfdState(
            frequency    = words_to_float(regs[0], regs[1]),
            current      = words_to_float(regs[4], regs[5]),
            speed        = words_to_float(regs[8], regs[9]),
            running      = bool(s & 0x0001),
            forward      = bool(s & 0x0002),
            reverse      = bool(s & 0x0004),
            at_reference = bool(s & 0x0008),
            fault        = bool(s & 0x0040),
            fault_code   = regs[27],
        )

    def read_all(self) -> dict[str, VfdState]:
        return {name: self.read_state(name) for name in self.clients}

    def set_frequency(self, name: str, hz: float) -> bool:
        hi, lo = float_to_words(hz)
        r = self.clients[name].write_registers(address=101, values=[hi, lo], device_id=1)
        return not r.isError()

    def control(self, name: str, word: int) -> bool:
        r = self.clients[name].write_register(address=100, value=word, device_id=1)
        return not r.isError()

    def run_forward(self, name): return self.control(name, 1)
    def run_reverse(self, name): return self.control(name, 3)
    def stop(self, name):        return self.control(name, 0)
    def fault_reset(self, name):
        self.control(name, 8)
        time.sleep(0.2)
        return self.control(name, 0)
```

---

### Etapa 2 — Teste Básico (15 min)

Crie `01_test.py`:

```python
"""
Etapa 2: testa conexão e leitura nos 3 VFDs.
"""
from multi_vfd import MultiVfd

VFDS = {
    "VFD1": ("192.168.1.51", 5020),
    "VFD2": ("192.168.1.52", 5020),
    "VFD3": ("192.168.1.53", 5020),
}

mv = MultiVfd(VFDS)
conn = mv.connect_all()
print("Conexões:", conn)

for name in VFDS:
    s = mv.read_state(name)
    if s:
        print(f"  {name}: f={s.frequency:.1f}Hz  RUN={s.running}")
    else:
        print(f"  {name}: ERRO")

mv.close_all()
```

Execute. Os 3 VFDs devem ser lidos. Cada smartphone mostra **1 cliente conectado**.

> **Atenção:** se o smartphone mostra 0 clientes ao final, é normal — o script desconecta no `close_all()`.

---

### Etapa 3 — Partida Sequencial (30 min)

**Cenário:** linha de produção com 3 motores. Para evitar pico de demanda elétrica, eles iniciam **em sequência**, com 5 segundos de espaçamento.

Crie `02_sequencial_start.py`:

```python
"""
Etapa 3: partida sequencial de 3 motores.
"""
from multi_vfd import MultiVfd
import time

VFDS = {
    "VFD1": ("192.168.1.51", 5020),
    "VFD2": ("192.168.1.52", 5020),
    "VFD3": ("192.168.1.53", 5020),
}

TARGET_FREQ = 40.0
INTERVAL = 5.0


def main():
    mv = MultiVfd(VFDS)
    mv.connect_all()

    try:
        # Configura todos com a mesma frequência de referência
        for name in VFDS:
            mv.set_frequency(name, TARGET_FREQ)
            print(f"  ✓ {name}: frequência referência = {TARGET_FREQ} Hz")
        time.sleep(0.5)

        # Inicia sequencialmente
        for name in VFDS:
            print(f"\n>>> START {name}")
            mv.run_forward(name)
            for sec in range(int(INTERVAL)):
                # Monitora todos durante a espera
                states = mv.read_all()
                line = f"  t={sec+1}/{int(INTERVAL)}  "
                for n, s in states.items():
                    if s:
                        line += f"{n}: f={s.frequency:5.1f}Hz {'R' if s.running else '.'} "
                print(line)
                time.sleep(1)

        # Mantém todos rodando por 10s
        print("\n>>> Todos rodando — observando 10s")
        for sec in range(10):
            states = mv.read_all()
            line = f"  +{sec+1}s  "
            for n, s in states.items():
                if s:
                    line += f"{n}: f={s.frequency:5.1f}Hz I={s.current:4.1f}A  "
            print(line)
            time.sleep(1)

        # Para sequencialmente (ordem inversa)
        print("\n>>> Stop sequencial")
        for name in reversed(list(VFDS)):
            print(f"  STOP {name}")
            mv.stop(name)
            time.sleep(INTERVAL)
    finally:
        # Garantia
        for name in VFDS:
            mv.stop(name)
        mv.close_all()


if __name__ == "__main__":
    main()
```

Execute. **Observem nos 3 smartphones**: cada um inicia 5 segundos após o anterior. Bom para entender **sequenciamento temporal**.

---

### Etapa 4 — Balanceamento de Carga (30 min)

**Cenário:** estação de bombeamento. 3 bombas devem fornecer vazão total constante. Se uma falha, as outras compensam aumentando velocidade.

Crie `03_load_share.py`:

```python
"""
Etapa 4: load sharing entre 3 bombas.
A frequência total alvo = 120 Hz (soma).
Se uma bomba falha, as outras assumem a vazão.
"""
from multi_vfd import MultiVfd
import time

VFDS = {
    "VFD1": ("192.168.1.51", 5020),
    "VFD2": ("192.168.1.52", 5020),
    "VFD3": ("192.168.1.53", 5020),
}

TOTAL_FREQ_TARGET = 120.0  # Hz (soma das 3)
MAX_FREQ_PER_VFD  = 55.0    # Limite individual


def main():
    mv = MultiVfd(VFDS)
    mv.connect_all()

    try:
        # Inicia todos com 40 Hz (carga inicial dividida igualmente)
        for name in VFDS:
            mv.set_frequency(name, 40.0)
            mv.run_forward(name)
        time.sleep(2)

        # Loop de balanceamento
        for iteration in range(30):
            states = mv.read_all()
            active = [name for name, s in states.items() if s and s.running and not s.fault]
            n_active = len(active)

            if n_active == 0:
                print("  ⚠ Nenhum VFD ativo. Encerrando.")
                break

            target_per_vfd = min(TOTAL_FREQ_TARGET / n_active, MAX_FREQ_PER_VFD)
            print(f"\n[Iter {iteration+1}] Ativos: {n_active} — target individual: {target_per_vfd:.1f} Hz")

            for name in active:
                mv.set_frequency(name, target_per_vfd)
                s = states[name]
                print(f"  {name}: f_atual={s.frequency:5.1f}Hz → setpoint={target_per_vfd:.1f}Hz")

            # A cada 5 iterações, "simulamos" uma falha em VFD2 para ver redistribuição
            if iteration == 5:
                print("\n  [SIMULAÇÃO] Parando VFD2 (falha simulada)")
                mv.stop("VFD2")

            if iteration == 15:
                print("\n  [SIMULAÇÃO] Religando VFD2")
                mv.run_forward("VFD2")

            time.sleep(2)

    finally:
        for name in VFDS:
            mv.stop(name)
        mv.close_all()


if __name__ == "__main__":
    main()
```

Execute. **Observem nos 3 smartphones**:

- Iter 1–5: as 3 bombas em ~40 Hz cada (120 Hz total).
- Iter 6+: VFD2 para. VFD1 e VFD3 sobem para ~55 Hz cada (limitado pelo MAX_FREQ_PER_VFD).
- Iter 15+: VFD2 volta. Os três voltam a ~40 Hz.

> **Esse padrão é exatamente o que ocorre em sistemas reais de bombeamento redundante.** Vocês acabaram de implementar o conceito.

---

### Etapa 5 — Dashboard de Orquestração em Node-RED (45 min)

Agora visualizem essa orquestração em um dashboard.

**Configure 3 servidores Modbus** no Node-RED (cada um apontando para um IP).

**Para cada VFD**, crie um fluxo de leitura + decodificação (use o function da Prática 6 [07-pratica-vfd7-nodered.md], adaptando os IPs).

**No dashboard**, crie 3 colunas (uma por VFD), cada uma com:

- Gauge: Frequency
- Gauge: Current
- LEDs: RUN, FAULT
- Botão: START FWD, STOP

**Adicione um painel "Orquestrador"** com:

- **Slider master**: Frequência alvo para todos os VFDs (escreve simultaneamente nos 3)
- **Botão "START ALL"**: dispara start sequencial (delay de 3s entre cada)
- **Botão "STOP ALL"**: para todos imediatamente
- **Indicador "Frequência total"**: soma das 3 frequências

#### Função "START ALL" (function node disparado pelo botão)

```javascript
// Dispara 3 mensagens, espaçadas em 3s
node.send({ payload: 1, vfd: "VFD1" });
setTimeout(() => node.send({ payload: 1, vfd: "VFD2" }), 3000);
setTimeout(() => node.send({ payload: 1, vfd: "VFD3" }), 6000);
return null;
```

Use **switch** após o function para rotear `msg.vfd` para o Modbus Write correto.

---

### Etapa 6 — Rotação do Orquestrador (30 min)

Cada aluno passa pelo papel de Orquestrador:

- Aluno A executa a sequência completa (Etapas 2–5)
- Em seguida, Aluno B se senta no laptop do Orquestrador (ou usa seu próprio com os mesmos scripts)
- Repete a sequência
- Em seguida, Aluno C

Em cada rodada:
- Os outros 2 alunos **observam** nos seus laptops (criando seus próprios dashboards read-only, se desejarem) e nos smartphones que eles cuidam.
- Discutam diferenças de abordagem.

---

## 7. Critérios de Sucesso

A equipe completou esta prática se:

- ✅ Os 3 smartphones simulam VFDs simultaneamente, com 1 cliente em cada.
- ✅ A classe `MultiVfd` (Python) é capaz de ler e comandar os 3 VFDs.
- ✅ A **partida sequencial** (Etapa 3) funciona com espaçamento temporal correto.
- ✅ O **load sharing** (Etapa 4) redistribui a carga quando um VFD para.
- ✅ O **dashboard Node-RED** mostra os 3 VFDs e tem o painel master de orquestração.
- ✅ Cada aluno passou pelo papel de Orquestrador.

---

## 8. Discussão e Reflexão

1. **Arquitetura.** O Orquestrador roda 1 cliente que abre 3 conexões TCP. Em uma planta com **30 motores**, seria viável manter 30 conexões abertas a partir de 1 servidor? Quais limites práticos surgem?
2. **Falha.** No `03_load_share.py`, simulamos a falha parando o VFD. Em uma planta real, como detectar **falhas de comunicação** (cabo solto, smartphone fora do ar)? Pesquisem o conceito de **timeout** e **deadband**.
3. **Sincronização.** A partida sequencial usa `time.sleep()`. Quais problemas isso pode causar em um sistema de tempo real? Que alternativas existem?
4. **Coordenação humana vs. automática.** Compare a abordagem programática desta prática com uma planta onde **operadores humanos** ligariam manualmente cada motor. Quais riscos e quais ganhos?
5. **Reflexão.** Em qual etapa vocês perceberam que a comunicação Modbus TCP "passou a ser invisível"? Em que momento o protocolo é abstração suficiente para focar **só na lógica de negócio**?

---

## 9. Entregáveis (equipe)

Um relatório de equipe contendo:

1. **Tabela** com IPs e a rotação dos papéis ao longo da prática.
2. **Os 3 scripts Python** (`multi_vfd.py`, `02_sequencial_start.py`, `03_load_share.py`) com comentários.
3. **Capturas de tela** do dashboard Node-RED de orquestração em pelo menos 3 momentos:
   - Todos parados
   - Partida sequencial em progresso
   - Load sharing após falha simulada
4. **Vídeo curto (3–4 min)** mostrando os 3 smartphones operando em sincronismo (preferencialmente filmando os 3 lado a lado).
5. **Análise quantitativa**: a partir dos logs do `03_load_share.py`, calcule:
   - Frequência total média antes e durante a "falha"
   - Tempo de resposta do balanceamento (segundos entre VFD2 parar e os outros aumentarem)
6. **Respostas** às 5 perguntas da seção 8.

---

## 10. Solução de Problemas

| Sintoma | Causa | Solução |
|---------|-------|---------|
| Apenas 2 VFDs respondem | 3º smartphone com problema | Verifique IP, ping, REMOTE |
| Latência crescente nas leituras | Lendo demais em loop apertado | Aumente `time.sleep()` entre iterações |
| Frequência total não bate com soma | Read e write em momentos diferentes | Aceito; defasagem de 1 ciclo |
| VFD trava em fault | Algum threshold disparado | Use `fault_reset()` do MultiVfd |
| Botão "START ALL" no Node-RED não funciona | Switch mal-configurado | Verifique rotas baseadas em `msg.vfd` |

---

## 11. Próximas Práticas

- **[Prática Grupo 3 — 3 clientes, 3 VFDs](10-pratica-grupo-3-3clientes-3vfds.md)**: cada aluno controla seu próprio VFD, mas vê todos.
- **[Prática Grupo 4 — Mini-planta integrada](11-pratica-grupo-4-mini-planta.md)**: papéis distintos com 2 VFDs + 1 medidor.

---

**Boa orquestração!**

— **Prof. Dênis Leite**
*Mekatronik — Advanced Engineering*
