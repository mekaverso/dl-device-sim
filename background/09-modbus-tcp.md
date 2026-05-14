# Módulo 9 — Modbus TCP: O Modbus Sobre Ethernet

> *"Pegue o Modbus, tire o CRC, envelope com TCP/IP. Pronto: Modbus TCP."*

## Objetivos de aprendizagem

Ao final deste módulo, o aluno será capaz de:

1. Descrever a estrutura do cabeçalho **MBAP** e justificar cada campo.
2. Explicar as diferenças entre Modbus RTU e Modbus TCP no nível do frame.
3. Implementar mentalmente uma transação Modbus TCP, byte a byte.
4. Compreender por que múltiplos clientes podem operar simultaneamente em Modbus TCP.
5. Identificar e justificar o uso da porta 502 (e variantes).

---

## 9.1 De Onde Veio o Modbus TCP

Em **1996**, a Schneider Electric (proprietária da Modicon) percebeu que a Ethernet estava se tornando ubíqua nas fábricas. Em vez de criar um protocolo totalmente novo, fizeram algo elegante:

> **Pegaram o frame Modbus RTU, removeram o CRC, adicionaram um pequeno cabeçalho (MBAP) e encapsularam dentro de TCP.**

Resultado: **Modbus TCP** — totalmente compatível semanticamente com o RTU, mas operando sobre IP.

Por que essa abordagem foi genial?

1. **Equipamentos legados** podiam ser modernizados com um **gateway RTU↔TCP** simples.
2. **Desenvolvedores** que já dominavam Modbus RTU adaptaram-se em minutos.
3. **Bibliotecas existentes** foram facilmente portadas.
4. **Networking moderno** (switches, Wi-Fi, fibra) tornou-se disponível instantaneamente.

A especificação foi publicada como **"Modbus Messaging on TCP/IP Implementation Guide V1.0"** e mais tarde formalizada como **IEC 61158** (parcialmente).

---

## 9.2 A Anatomia do Frame Modbus TCP

```
   ┌─────────────────────────────────────────┬─────────────────────┐
   │            MBAP Header (7 bytes)        │  Function + Data    │
   └─────────────────────────────────────────┴─────────────────────┘
        ↑                                      ↑
        │                                      │
   Modbus TCP                               PDU (Protocol Data Unit)
   prefix                                   = Mesma estrutura do RTU
                                              (sem CRC)
```

### 9.2.1 MBAP Header (Modbus Application Protocol)

| Campo            | Tamanho | Descrição                                      |
|------------------|---------|------------------------------------------------|
| Transaction ID   | 2 bytes | Identificador único por transação              |
| Protocol ID      | 2 bytes | Sempre 0x0000 para Modbus                      |
| Length           | 2 bytes | Número de bytes que **seguem** (Unit ID + PDU) |
| Unit ID          | 1 byte  | Equivalente ao slave address do RTU            |

### 9.2.2 Por que cada campo existe?

**Transaction ID** — Permite que **múltiplas requisições estejam "em voo" simultaneamente**. O cliente pode enviar 5 requisições antes de receber qualquer resposta; cada resposta carrega o Transaction ID correspondente, e o cliente sabe à qual pergunta ela se refere.

Em Modbus RTU isso era impossível: half-duplex e correlação implícita por timing.

**Protocol ID** — Reservado para futuras extensões. Sempre 0x0000 em Modbus TCP padrão.

**Length** — Permite que o receptor saiba **quantos bytes ler** do socket TCP. (TCP é stream-oriented; sem esse campo, seria difícil delimitar frames.)

**Unit ID** — Originalmente desnecessário em TCP (já temos IP para endereçar), mas mantido por compatibilidade com gateways RTU↔TCP. Em redes Modbus TCP puras, geralmente é fixo em 1.

---

## 9.3 Comparação Direta — RTU vs. TCP

Mesma operação: ler 2 input registers a partir do endereço 0 do escravo 1.

### Em RTU (8 bytes)

```
   01  04  00 00  00 02  71 CB
   ↑   ↑   ↑      ↑      ↑
   │   │   │      │      └── CRC-16 (Modbus)
   │   │   │      └────────── Quantidade = 2
   │   │   └───────────────── Endereço = 0
   │   └───────────────────── Function code
   └───────────────────────── Slave address
```

### Em TCP (12 bytes no payload Modbus)

```
   00 01 | 00 00 | 00 06 | 01 | 04 | 00 00 | 00 02
   ▲       ▲       ▲       ▲    ▲    ▲       ▲
   │       │       │       │    │    │       └── Quantidade
   │       │       │       │    │    └────────── Endereço
   │       │       │       │    └─────────────── Function code
   │       │       │       └──────────────────── Unit ID
   │       │       └──────────────────────────── Length = 6 (Unit ID + 5 bytes da PDU)
   │       └──────────────────────────────────── Protocol ID = 0
   └──────────────────────────────────────────── Transaction ID = 1
```

**Observações importantes:**

- O frame TCP tem **mais 6 bytes** (o MBAP), mas **não tem CRC** — o TCP/IP garante integridade.
- **Tamanho total da requisição na rede:** considerando overhead Ethernet+IP+TCP, são ~70 bytes para 12 bytes de Modbus.
- **Eficiência relativa:** baixa para uma transação pequena, **excelente para múltiplas transações simultâneas**.

---

## 9.4 Transação Completa — Exemplo Anotado

### Cenário

- Cliente: PC com EasyModbusTCP, IP 192.168.1.20
- Servidor: phone Android com ModbusDeviceSIM, IP 192.168.1.45, porta 5020
- Operação: ler Voltage L1-N (Input Register 0–1, FLOAT32)

### Passo 1 — three-way handshake

```
   Cliente              Servidor
      │                    │
      │ ── SYN (porta 5020) ──►│
      │                    │
      │ ◄── SYN+ACK ────── │
      │                    │
      │ ── ACK ──────────► │
      │                    │
      ✓ Conexão TCP estabelecida
```

### Passo 2 — Requisição Modbus

```
   Cliente envia (no payload TCP):

   00 01  00 00  00 06  01  04  00 00  00 02
   ↑      ↑      ↑      ↑   ↑   ↑      ↑
   │      │      │      │   │   │      └── Qty: 2
   │      │      │      │   │   └───────── Addr: 0
   │      │      │      │   └────────────── FC: 04 (read input registers)
   │      │      │      └────────────────── Unit ID: 1
   │      │      └────────────────────────── Length: 6
   │      └────────────────────────────────  Protocol ID: 0
   └─────────────────────────────────────── Trans ID: 1
```

### Passo 3 — Resposta Modbus

Tensão L1-N = 224.0 V = 0x43600000

```
   Servidor envia:

   00 01  00 00  00 07  01  04  04  43 60  00 00
   ↑      ↑      ↑      ↑   ↑   ↑   ↑      ↑
   │      │      │      │   │   │   │      └── Reg 1 (low word) = 0x0000
   │      │      │      │   │   │   └───────── Reg 0 (high word) = 0x4360
   │      │      │      │   │   └──────────── Byte count: 4
   │      │      │      │   └────────────────  FC eco: 04
   │      │      │      └────────────────────  Unit ID eco
   │      │      └────────────────────────────  Length: 7 (= 1 Unit ID + 6 bytes de PDU)
   │      └────────────────────────────────── Protocol ID: 0
   └─────────────────────────────────────────  Trans ID eco: 1
```

> **Importante:** O **Transaction ID na resposta** é **idêntico** ao da requisição. É assim que o cliente correlaciona resposta à pergunta.

### Passo 4 — Decodificação no cliente

```
   Reg 0 = 0x4360
   Reg 1 = 0x0000

   Concatenação ABCD: 0x43600000

   IEEE 754 → 224.0  ✓
```

---

## 9.5 Por Que Não Há CRC?

Em RTU, o CRC-16 protege contra corrupção elétrica no canal serial. Em TCP/IP:

- O **IP** tem um checksum próprio (header)
- O **TCP** tem um checksum próprio (header + payload)
- O **Ethernet** tem um CRC-32 no quadro físico

São **três camadas de verificação independentes**. Adicionar um CRC-16 Modbus seria redundância sem ganho prático.

> Embora algumas implementações conservadoras ainda adicionem um CRC opcional após o payload Modbus, **a especificação oficial não usa CRC em Modbus TCP**.

---

## 9.6 Múltiplas Conexões Simultâneas

Esta é uma das maiores diferenças funcionais entre Modbus RTU e Modbus TCP.

### Em RTU

- **Um único mestre** por barramento.
- **Todas as transações** são serializadas.
- **Aproximadamente 30 transações/segundo** em 9600 baud.

### Em TCP

- **Múltiplos clientes** podem se conectar **simultaneamente** ao mesmo servidor.
- Cada cliente abre sua **própria conexão TCP**.
- **Centenas de transações/segundo** são atingíveis.
- Servidores típicos suportam de **4 a 32 conexões simultâneas**.

> No **ModbusDeviceSIM**, o servidor aceita até 5 conexões simultâneas (configurado em `ModbusTcpServer.kt`). O contador de clientes na interface do app reflete isso.

### Implicação prática

Uma planta pode ter **simultaneamente**:
- HMI (operador)
- SCADA (supervisão)
- IHM móvel (técnico)
- Histórico (banco de dados)
- Manutenção (notebook do engenheiro)

Todos lendo do mesmo CLP via Modbus TCP, **sem conflito**, ao mesmo tempo. Isso é **revolucionário** em comparação com RTU.

---

## 9.7 Porta 502 e Suas Variantes

| Porta  | Uso                                                     |
|--------|----------------------------------------------------------|
| 502    | Modbus TCP padrão (texto claro, sem segurança)          |
| 802    | Modbus TCP **Secure** (TLS, encriptado)                  |
| 5020   | Variante não-padrão, comum em testes (também em **ModbusDeviceSIM** após patch) |

### 9.7.1 Por que 502?

Atribuído pela IANA (*Internet Assigned Numbers Authority*) à Schneider Electric/Modicon como porta oficial do Modbus TCP, em 1996. É a porta padrão e **deve ser preferida** quando viável.

### 9.7.2 Quando usar outra porta?

- **Porta 502 bloqueada por sistema operacional** (Android OEM restrito)
- **Porta 502 já ocupada** por outro processo
- **Múltiplos servidores Modbus** no mesmo equipamento (raro)
- **Esconder** o serviço de scanners superficiais (segurança por obscuridade — **não recomendada como única defesa**)

### 9.7.3 Convenção em ferramentas

| Ferramenta           | Porta padrão configurada |
|----------------------|--------------------------|
| EasyModbusTCP        | 502                      |
| pymodbus client/server | 502                    |
| Node-RED Modbus nodes | 502                     |
| ModbusDeviceSIM (Android) | **5020** (após patch) |

---

## 9.8 Modbus TCP com Múltiplos Unit IDs (Gateway Mode)

Há um caso de uso especial: **gateways Modbus TCP ↔ Modbus RTU**.

```
   Cliente (PC, IP=192.168.1.20)
            │
            │ TCP, porta 502
            │
            ▼
        Gateway
       (IP=192.168.1.100)
            │
            │ RS-485
            │
       ┌────┼────┬────────┐
       │    │    │        │
      Esc1 Esc2 Esc3  ... EscN
```

O cliente faz uma conexão TCP ao gateway, mas o **Unit ID** do MBAP indica qual escravo RTU é o destino real. O gateway:

1. Recebe a requisição TCP
2. Constrói o equivalente RTU usando o Unit ID como slave address
3. Envia pela serial
4. Espera resposta
5. Envelopa de volta em MBAP com o mesmo Transaction ID
6. Envia ao cliente TCP

Por isso o **Unit ID existe**: para suportar gateways. Em redes Modbus TCP puras (sem RTU atrás), você costuma ver Unit ID = 1 fixo.

---

## 9.9 Tamanho Máximo de PDU

A PDU Modbus TCP tem o **mesmo limite teórico** que RTU: **253 bytes** (256 menos os 3 bytes de slave addr + CRC do RTU).

Com o MBAP de 7 bytes:

- **Tamanho total máximo de um frame Modbus TCP:** 7 + 253 = **260 bytes**
- **Máximo de registradores lidos por requisição:** 125 (mesmo que RTU)
- **Máximo de registradores escritos por FC16:** 123

---

## 9.10 Sequência de Bytes — Endian

Modbus TCP herda do RTU a convenção **big-endian** (MSB primeiro) em **todos os campos de protocolo**:

- Transaction ID: big-endian
- Protocol ID: big-endian
- Length: big-endian
- Endereço de registrador: big-endian
- Quantidade: big-endian

**Dentro dos dados de registradores**, o byte order do conteúdo (FLOAT32, INT32) depende da **convenção do equipamento** — não do protocolo. Veja Módulo 5 sobre ABCD vs. CDAB.

---

## 9.11 Detalhe de Implementação — Por Que TCP Pode "Quebrar" Frames

TCP é um protocolo **de stream**, não de mensagem. O TCP pode:

- **Entregar um frame Modbus em múltiplos `recv()`**
- **Combinar dois frames Modbus em uma única chamada de `recv()`**

**O cliente deve sempre**:
1. Ler **7 bytes** do MBAP primeiro
2. Extrair o **Length**
3. Ler **mais (Length − 1)** bytes (= 1 unit ID + payload)
4. Processar o frame

**Não** assumir que cada `recv()` retorna um frame completo.

### Pseudocódigo correto

```python
def read_modbus_frame(sock):
    mbap = b''
    while len(mbap) < 7:
        chunk = sock.recv(7 - len(mbap))
        if not chunk:
            raise ConnectionError("socket closed")
        mbap += chunk

    length = int.from_bytes(mbap[4:6], 'big')
    payload = b''
    while len(payload) < length - 1:
        chunk = sock.recv((length - 1) - len(payload))
        if not chunk:
            raise ConnectionError("socket closed")
        payload += chunk

    return mbap + payload
```

---

## 9.12 Modbus TCP Secure (Modbus/TCP Security)

Lançado em **2018**, é a variante criptografada do Modbus TCP. Usa **TLS 1.2+** sobre TCP.

- **Porta:** 802 (oficial)
- **Autenticação:** certificados X.509 mútuos (cliente e servidor)
- **Criptografia:** AES-128/256
- **Integridade:** HMAC

> **Adoção em 2026:** ainda baixa. A maioria das instalações usa Modbus TCP "puro" e protege com VPN ou segmentação de rede. Mas a tendência é crescer com a pressão por segurança em **OT (Operational Technology)**.

---

## 9.13 Análise Captura em Wireshark

Capture com Wireshark um frame Modbus TCP. Você verá algo como:

```
   Frame 1: 80 bytes on wire
       Source: 192.168.1.20, Destination: 192.168.1.45
       Source Port: 54321, Destination Port: 5020
       [Modbus/TCP]
           Transaction ID: 1
           Protocol ID: 0
           Length: 6
           Unit ID: 1
           Function Code: Read Input Registers (4)
           Reference Number: 0
           Word Count: 2
```

O Wireshark **decodifica automaticamente** o Modbus se reconhecer a porta. Se sua porta não é 502, vá em **Analyze → Decode As** e force a interpretação como Modbus.

---

## 9.14 Diagnóstico — Problemas Comuns em Modbus TCP

| Sintoma                                | Causas prováveis                                                |
|----------------------------------------|------------------------------------------------------------------|
| Cliente não conecta                    | IP errado, firewall bloqueando, porta errada                    |
| Conexão estabelece mas timeout em read | Servidor parado; Unit ID incorreto                              |
| Resposta com dados estranhos           | Byte order incorreto (ABCD vs CDAB); FC errado (FC03 vs FC04)   |
| "Connection reset by peer"             | Servidor crashou, ou rejeitou (firewall ativo)                  |
| Latência alta (centenas de ms)         | Rede congestionada; servidor sobrecarregado                     |
| Funciona em LAN, falha em WAN          | NAT, port forwarding ausente, ISP bloqueando porta 502          |
| Conexão alterna entre OK e falha       | Cabo Ethernet com defeito; switch com problema; Wi-Fi instável  |

---

## 9.15 Roteiro do Laboratório 9.1 — Modbus TCP com ModbusDeviceSIM

### Material

- 1 smartphone Android com ModbusDeviceSIM instalado
- 1 PC com EasyModbusTCP
- Mesma rede Wi-Fi

### Procedimento

1. **No smartphone**, abra o app, selecione **MK-EM3P**, toque START.
2. Anote o IP exibido (ex.: `10.65.154.50:5020`).
3. **No PC**, abra EasyModbusTCP.
4. Configure:
   - Host: IP do smartphone
   - Porta: **5020**
   - Unit ID: **1**
5. Conecte. O contador de clientes no app sobe para 1.
6. **Leia** registradores 0–91 com **FC04** (Read Input Registers).
7. Veja os valores brutos.
8. **Capture com Wireshark** uma única transação. Identifique:
   - O three-way handshake
   - O frame Modbus
   - A resposta
9. **Decodifique** manualmente um FLOAT32 a partir de dois registradores adjacentes.
10. **Escreva** um valor em um Holding Register (FC06) e verifique a confirmação.

---

## 9.16 Exercícios

### Conceituais

1. Por que Modbus TCP **não usa CRC** mas Modbus RTU usa?
2. Explique a função de **cada campo** do MBAP Header.
3. Por que o **Transaction ID** permite múltiplas requisições simultâneas?

### Construção de frames

4. Construa o frame Modbus TCP completo (em hex) para:
   - Ler 5 holding registers a partir do endereço 100, Unit ID 2, Transaction ID 47.
   - Escrever o valor 0x1234 no holding register 50, Unit ID 1, Transaction ID 100.
5. Construa a resposta esperada para cada um dos casos acima.

### Análise

6. Você capturou no Wireshark o seguinte payload TCP:
   ```
   00 5A 00 00 00 06 01 03 00 00 00 0A
   ```
   - Qual o Transaction ID?
   - Qual a função?
   - Quantos registradores estão sendo lidos?
   - Construa a **resposta** esperada (escolha valores arbitrários para os registradores).

### Diagnóstico

7. Você consegue **pingar** um IP de um inversor, mas o EasyModbusTCP não consegue conectar à porta 502. Liste 5 hipóteses possíveis e como investigar cada uma.
8. Em uma rede com 10 medidores Modbus TCP, um único medidor apresenta **latência alta** intermitente (3 segundos). Diagnóstico provável?

### Projeto

9. **Em pymodbus**, escreva um script que abra **3 conexões simultâneas** ao mesmo servidor Modbus TCP e leia registradores diferentes em paralelo (usando threads ou async). Compare o tempo total com a versão sequencial.

### Reflexão

10. **Discussão.** Modbus TCP elimina a necessidade de Modbus RTU em plantas novas? Em quais cenários RTU ainda faz sentido?

---

## 9.17 Síntese

- Modbus TCP = Modbus PDU + MBAP header (7 bytes), sobre TCP/IP, porta **502**.
- **Sem CRC** — o TCP cuida da integridade.
- **Multi-cliente**: cada conexão é independente.
- **Transaction ID** correlaciona requisição e resposta, permitindo simultaneidade.
- **Length** delimita o frame dentro do stream TCP.
- **Unit ID** sobrevive para suporte a gateways RTU↔TCP.

---

**Próximo módulo:** [10-praticas-visao-geral.md](10-praticas-visao-geral.md) — orientação para escolher e executar as 7 práticas de laboratório.
