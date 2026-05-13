# Módulo 10 — Práticas de Laboratório

> *"Em automação, ler é necessário, mas é no laboratório que o aprendizado se solidifica."*

## Visão Geral

Este módulo contém **8 práticas estruturadas** que percorrem toda a disciplina, da comunicação serial básica ao Modbus TCP integrado com ferramentas modernas (Python, Node-RED).

Cada prática tem o mesmo formato:

- **Objetivos** específicos
- **Material** necessário
- **Pré-requisitos** teóricos
- **Procedimento** passo a passo
- **Entregáveis** (o que ir no relatório)
- **Discussão** (perguntas para reflexão)

---

## Lab 01 — Comunicação Serial Básica com RS-232

**Vinculação teórica:** Módulos 2 e 3.

### Objetivos

1. Configurar uma porta serial e estabelecer comunicação entre dois computadores.
2. Observar visualmente o frame UART em um analisador lógico (ou software equivalente).
3. Validar o efeito de **baud rate**, **paridade** e **stop bits** mal-configurados.

### Material

- 2 PCs com Windows ou Linux
- 2 conversores USB-RS232
- 1 cabo **null modem** DB-9 (ou adaptador cruzado)
- Software de terminal: **PuTTY**, **RealTerm** ou **Termite**
- (Opcional) Analisador lógico: Saleae, ZeroPlus, ou software como **Sigrok**

### Procedimento

#### Parte A — Estabelecer comunicação

1. Identifique a porta COM de cada conversor (Gerenciador de Dispositivos no Windows).
2. Conecte os dois PCs com o cabo null modem.
3. Abra o terminal em ambos: **9600 baud, 8N1, sem fluxo**.
4. Digite caracteres em PC1; confirme que aparecem em PC2 e vice-versa.

#### Parte B — Investigar mau-configuração

5. Mude o baud rate de PC2 para **4800**. O que acontece com os caracteres recebidos?
6. Volte para 9600. Mude a paridade de PC2 para **Even**, mantendo PC1 em **None**.
7. Mude a paridade de PC1 e PC2 para **Even**. Comunicação volta?

#### Parte C — Captura visual

8. (Se houver analisador lógico) Conecte sondas em **TX, RX, GND**. Configure aquisição a 10× a taxa de bit (96 kSamples/s para 9600 baud).
9. Digite o caractere **'A'**. Capture o sinal. Identifique:
   - Start bit
   - Bits de dados (LSB primeiro)
   - Stop bit
   - Duração total
10. Repita para o caractere **'M'** e calcule o bit de paridade que apareceria em modo Even.

### Entregáveis

- Tabela com os resultados das Partes A e B
- Capturas (Parte C) com anotações
- Discussão: por que o terminal mostra caracteres "estranhos" quando o baud rate está errado?

### Discussão

- Calcule a **taxa máxima de transmissão útil** em bytes/s para 9600 baud, 8N1.
- O que aconteceria se ambos os PCs estivessem em 8E1 mas com a paridade calculada de modos opostos (par vs ímpar)?

---

## Lab 02 — Comunicação RS-485 em Multidrop

**Vinculação teórica:** Módulo 4.

### Objetivos

1. Montar uma rede RS-485 com **3 nós**.
2. Avaliar o efeito de **terminação** e **polarização** na qualidade do sinal.
3. Compreender o conceito de half-duplex na prática.

### Material

- 3 PCs (ou 2 PCs + 1 Arduino com conversor TTL-RS485)
- 3 conversores USB-RS485
- 5 metros de cabo UTP cat 5e
- 2 resistores de **120 Ω** (terminação)
- 2 resistores de **680 Ω** (bias, opcional)
- Multímetro

### Procedimento

#### Parte A — Conexão sem terminadores

1. Conecte os 3 conversores em **bus linear**: cada A juntos, cada B juntos.
2. Não coloque terminadores ainda.
3. Abra terminal em cada PC, **9600 baud, 8N1**.
4. Em PC1, digite caracteres. Veja-os aparecer em PC2 e PC3.
5. Verifique que digitar em **dois PCs simultaneamente** corrompe a comunicação (colisão).

#### Parte B — Efeito da terminação

6. Aumente o baud rate para **115200**. A comunicação ainda funciona?
7. Adicione **um terminador de 120 Ω** em cada extremidade do barramento.
8. Repita o teste em 115200.

#### Parte C — Medições

9. Com a comunicação em silêncio, meça com voltímetro a **tensão entre A e B**. Deve haver flutuação aleatória (sem bias).
10. Adicione o circuito de bias (+5V — 680Ω — A; B — 680Ω — GND). Meça novamente.

### Entregáveis

- Foto da montagem
- Tabela com taxas de erro com/sem terminador
- Tensão medida com/sem bias
- Discussão sobre half-duplex

### Discussão

- Por que o sistema funciona em 9600 sem terminação mas falha em 115200?
- Qual o impacto da **distância** entre nós? E o tamanho dos **stubs**?

---

## Lab 03 — Modbus RTU com Simulador

**Vinculação teórica:** Módulo 6.

### Objetivos

1. Estabelecer comunicação Modbus RTU entre um simulador (ModbusDeviceSIM em Python) e um cliente (EasyModbus ou pymodbus).
2. Decodificar frames brutos.
3. Calcular CRC-16 manualmente e validar.

### Material

- 1 PC com **ModbusDeviceSIM** (Python desktop)
- **com0com** instalado (porta serial virtual no Windows)
- **EasyModbus** ou script Python com **pymodbus**
- (Opcional) Sniffer serial: **PortMon** ou **RealTerm**

### Procedimento

#### Parte A — Setup

1. Configure com0com criando par **COM10 ↔ COM11**.
2. Inicie ModbusDeviceSIM com transporte **Modbus RTU em COM10**, escravo 1, MK-EM3P, 9600 baud 8E1.
3. Inicie EasyModbus em **COM11**, mesma configuração.

#### Parte B — Leituras

4. Leia **Input Registers** 0–91 (FC04). Veja todas as medições brutas.
5. Decode mentalmente o **FLOAT32** de Voltage L1-N (regs 0–1) usando ordem ABCD. Confirme o valor.
6. Leia **Holding Registers** 100–121 (FC03). Identifique CT Primary (reg 100), Over-Voltage Threshold (107–108).

#### Parte C — Escrita

7. Escreva **200** no Holding Register 100 (CT Primary) com FC06.
8. Releia para confirmar.
9. Escreva o FLOAT32 **260.0** nos Holding Registers 107–108 com FC16. Calcule os valores hex e use as conversões adequadas.

#### Parte D — Análise do frame

10. Ative o sniffer serial em PortMon ou similar.
11. Capture um frame de **leitura de 2 registradores** (FC04). Anote:
    - Slave address
    - Function code
    - Start address (high, low)
    - Quantity (high, low)
    - CRC (low, high)
12. **Calcule manualmente** o CRC-16 do frame. Confirme que bate com o capturado.

#### Parte E — Exceções

13. Tente ler o endereço **9999**. Capture a resposta.
14. Identifique:
    - O bit 7 ligado na function code (= erro)
    - O código de exceção (esperado: 0x02 — Illegal Data Address)

### Entregáveis

- Captura dos frames brutos
- Cálculo manual de CRC com passos
- Tabela com valores lidos (raw e decodificados)
- Discussão dos resultados

### Discussão

- O que aconteceria se você tentasse escrever em um Input Register?
- Por que o CRC é transmitido com LSB primeiro?

---

## Lab 04 — Modbus TCP com ModbusDeviceSIM (Android)

**Vinculação teórica:** Módulo 9.

### Objetivos

1. Estabelecer comunicação Modbus TCP entre um servidor móvel (ModbusDeviceSIM no Android) e cliente PC.
2. Comparar o frame TCP ao equivalente RTU.
3. Usar Wireshark para visualizar a comunicação.

### Material

- 1 smartphone Android com **ModbusDeviceSIM** instalado
- 1 PC com **EasyModbusTCP** e **Wireshark**
- Mesma rede Wi-Fi (smartphone e PC na mesma subrede)

### Procedimento

#### Parte A — Setup

1. No smartphone, abra ModbusDeviceSIM, selecione **MK-EM3P**, toque START.
2. Anote o IP exibido (ex.: `10.65.154.50:5020`).
3. No PC, abra **Wireshark**, capture na interface Wi-Fi.
4. Filtro: `tcp.port == 5020`.
5. No PC, abra EasyModbusTCP. Configure host, porta **5020**, Unit ID **1**.
6. Conecte.

#### Parte B — Análise do handshake

7. No Wireshark, identifique:
   - SYN (cliente → servidor)
   - SYN+ACK (servidor → cliente)
   - ACK (cliente → servidor)
   - Tempo total do handshake (delta entre SYN e ACK final)

#### Parte C — Leituras

8. Em EasyModbusTCP, leia 2 registradores a partir de 0 com FC04.
9. No Wireshark, capture o frame Modbus. Identifique:
   - Transaction ID
   - Protocol ID
   - Length
   - Unit ID
   - Function code
   - Start address
   - Quantity
10. Identifique a **resposta** do servidor e correlacione pelo Transaction ID.

#### Parte D — Múltiplos clientes

11. Abra **uma segunda instância** de EasyModbusTCP (ou use Python). Conecte ao mesmo servidor.
12. No app, observe o contador de clientes subir para 2.
13. Faça leituras simultâneas. Confirme que ambos clientes recebem dados independentemente.

#### Parte E — Escrita

14. Conecte com o app em **modo VFD7**.
15. Escreva no Control Word (HR 100) valor **1** (RUN). Observe o motor "ligar" no app.
16. Mude para reverse com valor **3**.

### Entregáveis

- Captura do Wireshark anotada
- Comparação byte-a-byte com a equivalente RTU
- Cálculo do FLOAT32 a partir dos registradores brutos
- Discussão sobre múltiplos clientes

### Discussão

- Quantos bytes overhead há em Modbus TCP em comparação com Modbus RTU para a mesma operação?
- Por que múltiplos clientes funcionam em TCP mas não em RTU?

---

## Lab 05 — Cliente Modbus TCP em Python com pymodbus

**Vinculação teórica:** Módulos 8 e 9.

### Objetivos

1. Implementar um cliente Modbus TCP em Python.
2. Decodificar FLOAT32 programaticamente.
3. Construir um polling contínuo com tratamento de erros.

### Material

- PC com Python 3.10+, **pymodbus 3.x** instalado
- Servidor Modbus TCP (ModbusDeviceSIM no Android, ou versão Python)

### Procedimento

#### Parte A — Instalação

```bash
pip install pymodbus
```

#### Parte B — Cliente básico

Crie o arquivo `client_basic.py`:

```python
from pymodbus.client import ModbusTcpClient
import struct

HOST = "10.65.154.50"  # IP do smartphone
PORT = 5020
UNIT = 1


def words_to_float(high: int, low: int) -> float:
    """Combina dois registradores Modbus (ABCD) em um IEEE 754 float."""
    packed = struct.pack(">HH", high, low)
    return struct.unpack(">f", packed)[0]


def main():
    client = ModbusTcpClient(HOST, port=PORT)
    if not client.connect():
        print("Falha ao conectar")
        return

    # Lê 2 registradores a partir do endereço 0 (Voltage L1-N)
    result = client.read_input_registers(address=0, count=2, device_id=UNIT)

    if result.isError():
        print(f"Erro: {result}")
    else:
        v = words_to_float(result.registers[0], result.registers[1])
        print(f"Voltage L1-N: {v:.2f} V")

    client.close()


if __name__ == "__main__":
    main()
```

Execute e veja a tensão real lida do dispositivo.

#### Parte C — Polling contínuo

Crie `client_polling.py`:

```python
from pymodbus.client import ModbusTcpClient
import struct
import time

HOST = "10.65.154.50"
PORT = 5020
UNIT = 1


def words_to_float(h, l):
    return struct.unpack(">f", struct.pack(">HH", h, l))[0]


PARAMS = [
    (0,  "V L1-N",      "V"),
    (12, "I L1",        "A"),
    (26, "P Total",     "kW"),
    (50, "PF Total",    ""),
    (52, "Frequência",  "Hz"),
]


def main():
    client = ModbusTcpClient(HOST, port=PORT)
    client.connect()
    try:
        while True:
            for addr, name, unit in PARAMS:
                r = client.read_input_registers(address=addr, count=2, device_id=UNIT)
                if not r.isError():
                    v = words_to_float(r.registers[0], r.registers[1])
                    print(f"  {name:14}: {v:8.2f} {unit}")
                else:
                    print(f"  {name:14}: ERRO")
            print("-" * 40)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        client.close()


if __name__ == "__main__":
    main()
```

#### Parte D — Escrita de configuração

```python
from pymodbus.client import ModbusTcpClient
import struct

HOST = "10.65.154.50"; PORT = 5020; UNIT = 1

def float_to_words(value):
    packed = struct.pack(">f", value)
    return struct.unpack(">HH", packed)


client = ModbusTcpClient(HOST, port=PORT)
client.connect()

# Escreve 260.0 V no Over-Voltage Threshold (HR 107-108)
hi, lo = float_to_words(260.0)
client.write_registers(address=107, values=[hi, lo], device_id=UNIT)

# Releia para confirmar
r = client.read_holding_registers(address=107, count=2, device_id=UNIT)
print(f"Lido de volta: {r.registers}")  # Deve ser [0x4382, 0x0000]

client.close()
```

### Entregáveis

- Scripts Python comentados
- Capturas da saída
- Discussão: como você adicionaria tratamento robusto de erros (reconexão automática)?

### Discussão

- Em **quantos pontos diferentes** seu código falha se a rede cair? Como mitigar?
- Compare a velocidade de polling em pymodbus com a varredura via EasyModbusTCP.

---

## Lab 06 — Servidor Modbus TCP em Python

**Vinculação teórica:** Módulo 9.

### Objetivos

1. Implementar um servidor Modbus TCP em Python.
2. Compreender o lado servidor da equação.
3. Validar conectividade com clientes diversos.

### Material

- PC com Python 3.10+, pymodbus 3.x
- EasyModbusTCP (cliente)

### Procedimento

Crie `server_basic.py`:

```python
from pymodbus.server import StartTcpServer
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusServerContext,
    ModbusSequentialDataBlock,
)


# Bloco de 100 holding registers com valores iniciais
hr_block = ModbusSequentialDataBlock(0, [i * 10 for i in range(100)])

# Bloco de 100 input registers com valores iniciais
ir_block = ModbusSequentialDataBlock(0, [i * 100 for i in range(100)])

device = ModbusDeviceContext(
    di=ModbusSequentialDataBlock(0, [0] * 100),
    co=ModbusSequentialDataBlock(0, [0] * 100),
    hr=hr_block,
    ir=ir_block,
)
context = ModbusServerContext(devices={1: device}, single=False)


print("Servidor Modbus TCP rodando em 0.0.0.0:5020")
StartTcpServer(context=context, address=("0.0.0.0", 5020))
```

Execute. De outro PC ou da mesma máquina (loopback `127.0.0.1`), conecte com EasyModbusTCP em **porta 5020** e leia os registradores.

### Entregáveis

- Script comentado
- Captura do tráfego com Wireshark mostrando uma transação completa
- Diagrama da arquitetura cliente-servidor

### Discussão

- Qual a vantagem de implementar **seu próprio servidor** Modbus em vez de usar um pronto?
- Como você expandiria este servidor para **simular variações** ao longo do tempo (ex.: tensão oscilando)?

---

## Lab 07 — Integração Modbus TCP com Node-RED

**Vinculação teórica:** Módulos 8, 9.

### Objetivos

1. Instalar e configurar **Node-RED**.
2. Criar um **dashboard** que exibe medições Modbus TCP em tempo real.
3. Implementar **alarmes** baseados em thresholds.

### Material

- PC com **Node.js 18+** e **Node-RED**
- ModbusDeviceSIM rodando (Android ou Python)

### Procedimento

#### Parte A — Instalação

```bash
npm install -g node-red
node-red
```

Abra o navegador em `http://localhost:1880`.

#### Parte B — Instalar pacotes Modbus e Dashboard

No menu (≡) → **Manage palette** → **Install**:

- `node-red-contrib-modbus`
- `node-red-dashboard`

#### Parte C — Fluxo básico

Crie um fluxo com:

1. Nó **`inject`** configurado para repetir a cada 2 segundos.
2. Nó **`Modbus Read`** configurado:
   - Server: novo, host = IP do smartphone, porta 5020, unit ID 1
   - FC: **Read Input Registers** (FC04)
   - Address: 0
   - Quantity: 2
3. Nó **`function`** que decodifica FLOAT32:
   ```javascript
   const buffer = Buffer.alloc(4);
   buffer.writeUInt16BE(msg.payload[0], 0);
   buffer.writeUInt16BE(msg.payload[1], 2);
   msg.payload = buffer.readFloatBE(0);
   return msg;
   ```
4. Nó **`ui_gauge`** (Dashboard) — exibe a tensão.

Deploy. Abra o dashboard em `http://localhost:1880/ui`.

#### Parte D — Dashboard completo

Expandir o fluxo para ler:
- Tensão L1, L2, L3
- Corrente L1, L2, L3
- Potência Total
- Frequência

E criar gauges/charts para cada um.

#### Parte E — Alarme

Adicionar:
- Nó **`switch`** que filtra `payload > 240` (sobre tensão simulada).
- Nó **`ui_notification`** que mostra alerta.

### Entregáveis

- Captura do fluxo
- Captura do dashboard
- Script do nó `function`
- Discussão: vantagens do Node-RED como middleware industrial

### Discussão

- Compare Node-RED com SCADAs tradicionais. Onde cada um se encaixa?
- Como você integraria com **MQTT** para enviar dados à nuvem?

---

## Lab 08 — Modbus TCP Multi-cliente Concorrente

**Vinculação teórica:** Módulos 8, 9.

### Objetivos

1. Confirmar empiricamente que múltiplos clientes podem operar simultaneamente.
2. Medir desempenho com concorrência.
3. Discutir limites e boas práticas.

### Material

- ModbusDeviceSIM (servidor)
- 3+ clientes simultâneos (combinação de EasyModbusTCP, Python, Node-RED)

### Procedimento

1. Inicie o servidor (ModbusDeviceSIM).
2. Conecte **cliente 1**: EasyModbusTCP em polling de 100 ms.
3. Conecte **cliente 2**: script Python `client_polling.py` do Lab 05.
4. Conecte **cliente 3**: fluxo Node-RED do Lab 07.
5. Confirme no contador do app que há 3 clientes conectados.
6. **Em todos os clientes**, leia valores e verifique consistência.
7. **Provoque concorrência**: faça os 3 escreverem **valores diferentes** no mesmo Holding Register. Qual ganha?
8. Meça tempo de resposta com `time.time()` em Python para 100 leituras consecutivas em cada cenário:
   - Apenas cliente 1 conectado
   - 3 clientes conectados
9. Compare resultados.

### Entregáveis

- Tabela de tempo de resposta por cenário
- Discussão sobre concorrência de escrita
- Recomendações de design para integração industrial

### Discussão

- O servidor Modbus TCP do ModbusDeviceSIM é **thread-safe** nas escritas? Como você confirmaria?
- Qual a estratégia para evitar **race conditions** em ambientes multi-cliente?
- Em uma planta real, o que poderia dar errado com 3 sistemas (SCADA, HMI, manutenção) escrevendo no mesmo CLP?

---

## Avaliação dos Laboratórios

Cada lab vale **3,125 %** da nota total (8 labs × 3,125 % = 25 %).

**Critérios:**

- **30 %**: Execução técnica correta (a comunicação funciona, os valores estão certos)
- **30 %**: Qualidade do relatório (clareza, organização, capturas e diagramas)
- **20 %**: Análise crítica nas discussões
- **20 %**: Apresentação durante a aula (defesa oral)

---

## Recomendações Gerais para os Relatórios

1. **Capturas reais** — não apenas teóricas. Mostre o que **você** observou.
2. **Comparação com a teoria** — destaque divergências e justifique.
3. **Erros encontrados** — não esconda; documente como diagnosticou e resolveu.
4. **Conclusões pessoais** — o que você aprendeu além do que estava previsto?

---

**Próximo módulo:** [11-projeto-integrador.md](11-projeto-integrador.md)
