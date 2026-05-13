# Módulo 6 — Modbus RTU: Anatomia do Protocolo Serial

> *"Decifrar um frame Modbus RTU é como ler um pequeno romance: cada byte conta uma parte da história."*

## Objetivos de aprendizagem

Ao final deste módulo, o aluno será capaz de:

1. Descrever a estrutura completa de um frame Modbus RTU, byte a byte.
2. Calcular o **CRC-16 (Modbus)** manualmente para frames curtos.
3. Construir e interpretar requisições e respostas para as principais function codes.
4. Compreender os requisitos de **timing** (silêncio de 3,5T) e suas implicações.
5. Diagnosticar erros comuns em redes Modbus RTU.

---

## 6.1 Por Que "RTU"?

**RTU** = *Remote Terminal Unit*. O nome refere-se à arquitetura clássica de SCADA, em que um computador supervisor central consulta **terminais remotos** distribuídos pelo campo. Em Modbus, esse termo passou a designar a variante **serial binária** do protocolo.

A grande característica do Modbus RTU é a **eficiência**: cada byte transmitido carrega 8 bits úteis de informação. Compare com Modbus ASCII, que precisa de **2 caracteres ASCII** (16 bits no fio) para representar **cada byte**.

---

## 6.2 Estrutura do Frame Modbus RTU

```
   ┌──────────────┬──────────────┬─────────────────────┬──────────────┐
   │  Slave Addr  │  Function    │      Data           │   CRC-16     │
   │   1 byte     │   1 byte     │   N bytes (0–252)   │   2 bytes    │
   └──────────────┴──────────────┴─────────────────────┴──────────────┘
            ↑                                                    ↑
            │                                                    │
       silêncio                                              silêncio
       ≥ 3.5T                                                ≥ 3.5T
```

| Campo          | Tamanho | Descrição                                              |
|----------------|---------|--------------------------------------------------------|
| Slave Address  | 1 byte  | Endereço do escravo (0–247). 0 = broadcast             |
| Function Code  | 1 byte  | Operação solicitada (FC01, FC03, etc.)                |
| Data           | varia   | Dados específicos da função                            |
| CRC-16         | 2 bytes | Cyclic Redundancy Check, **little-endian** (LSB primeiro!) |

**Tamanho total máximo:** 256 bytes (limite herdado de Modbus Plus e mantido por compatibilidade).

### 6.2.1 Endereço do escravo

| Faixa     | Significado                                    |
|-----------|------------------------------------------------|
| 0         | **Broadcast** — todos os escravos respondem (sem resposta de volta) |
| 1 a 247   | Endereços válidos individuais                  |
| 248 a 255 | Reservados                                     |

> Em redes RS-485 reais, raramente se ultrapassa **32 escravos** (limite elétrico do RS-485 padrão), mas o protocolo permite até 247 endereçáveis.

### 6.2.2 Sobre o CRC ser little-endian

Atenção a este detalhe **clássico** que confunde iniciantes: enquanto os campos de dados Modbus são tipicamente **big-endian** (MSB primeiro), o **CRC é transmitido com o byte menos significativo primeiro** (little-endian).

```
   CRC calculado: 0x84A3
   No fio:        0xA3 (LSB)  0x84 (MSB)
```

Esta é uma idiossincrasia histórica. Lembre dela.

---

## 6.3 Timing: O Silêncio Como Delimitador

Modbus RTU **não tem caractere especial de início** ou fim. Como o receptor sabe quando termina um frame e começa o próximo?

**Pelo silêncio.** A especificação define dois intervalos críticos baseados no **tempo de transmissão de um caractere** (T = 11 bits a baud rate atual):

| Intervalo | Tempo                             | Significado                                |
|-----------|-----------------------------------|--------------------------------------------|
| t1.5      | ≥ 1,5 caracteres de silêncio      | Indica **erro de frame** (caractere "lento")|
| t3.5      | ≥ 3,5 caracteres de silêncio      | Indica **fim de frame**                    |

```
   Frame 1:
   [Slave][FC][Data...][CRC]
                              <─── ≥ 3.5 T de silêncio ──>
                                                            Frame 2:
                                                            [Slave][FC][Data...][CRC]
```

### 6.3.1 Cálculo de t3.5 em 9600 baud

```
   1 caractere (frame UART de 11 bits) = 11 / 9600 ≈ 1,146 ms
   t3.5 = 3,5 × 1,146 ≈ 4,01 ms
```

### 6.3.2 Exceção da especificação

Para baud rates **acima de 19200**, a especificação recomenda **fixar t3.5 em 1,75 ms** em vez de calcular proporcionalmente. Razão: em taxas muito altas, os intervalos calculados ficam tão pequenos que o sistema operacional do PC mestre não consegue garantir o silêncio. Manter um piso de 1,75 ms preserva a interoperabilidade.

### 6.3.3 Implicação prática

**Implementar Modbus RTU em PC com Windows é difícil.** O Windows não é um sistema operacional de tempo real; o agendador pode introduzir pausas de dezenas de ms a qualquer momento. Por isso, em aplicações sérias, prefere-se:

- **Microcontroladores** com timer dedicado para medir os intervalos
- **Gateways Modbus RTU → TCP** para tirar o PC da camada serial
- **Bibliotecas que reimplementam o timing em userspace** com workarounds

---

## 6.4 Function Codes em Detalhe

Vamos dissecar as **4 function codes essenciais**: FC01, FC03, FC04, FC06 e FC16.

### 6.4.1 FC03 — Read Holding Registers

**Requisição (mestre):**

```
   ┌──────┬──────┬────────────┬────────────┬──────┐
   │ Slv  │ 0x03 │ Start Addr │ Qty regs   │ CRC  │
   │ 1B   │ 1B   │  2B (MSB)  │  2B (MSB)  │ 2B   │
   └──────┴──────┴────────────┴────────────┴──────┘
```

**Resposta (escravo):**

```
   ┌──────┬──────┬───────────┬───────────────────────┬──────┐
   │ Slv  │ 0x03 │ Byte cnt  │ Register values       │ CRC  │
   │ 1B   │ 1B   │  1B       │  2×Qty bytes          │ 2B   │
   └──────┴──────┴───────────┴───────────────────────┴──────┘
```

**Exemplo:** Ler 2 registradores a partir do endereço 100 do escravo 5.

**Requisição:**
```
   05  03  00 64  00 02  4D 8C
   ↑   ↑   ↑      ↑      ↑
   │   │   │      │      └── CRC (calculado abaixo)
   │   │   │      └────────── Quantidade: 0x0002 = 2 registradores
   │   │   └───────────────── Endereço: 0x0064 = 100
   │   └───────────────────── Function code: 0x03
   └───────────────────────── Endereço do escravo: 5
```

**Resposta (se reg 100 = 0x012C = 300 e reg 101 = 0x00C8 = 200):**
```
   05  03  04  01 2C  00 C8  XX XX
   ↑   ↑   ↑   ↑      ↑      ↑
   │   │   │   │      │      └── CRC
   │   │   │   │      └───────── Reg 101 = 0x00C8
   │   │   │   └──────────────── Reg 100 = 0x012C
   │   │   └──────────────────── Byte count: 4 bytes
   │   └──────────────────────── FC eco
   └──────────────────────────── Endereço eco
```

### 6.4.2 FC04 — Read Input Registers

**Idêntico ao FC03**, mas a área lida é **Input Registers** em vez de Holding Registers. Apenas o byte de function code muda (0x04 em vez de 0x03).

> **Em MK-EM3P (ModbusDeviceSIM):** todas as medições (tensão, corrente, potência) estão em **Input Registers**, lidos com **FC04**.
> Os parâmetros de configuração (CT, VT, thresholds) estão em **Holding Registers**, lidos com **FC03** e escritos com **FC06/FC16**.

### 6.4.3 FC06 — Write Single Register

**Requisição:**

```
   ┌──────┬──────┬────────────┬────────────┬──────┐
   │ Slv  │ 0x06 │ Reg Addr   │ Reg Value  │ CRC  │
   │ 1B   │ 1B   │  2B (MSB)  │  2B (MSB)  │ 2B   │
   └──────┴──────┴────────────┴────────────┴──────┘
```

**Resposta:** **eco exato da requisição** (incluindo CRC, calculado novamente). É a forma do escravo confirmar.

**Exemplo:** Escrever 200 (0x00C8) no holding register 100 do escravo 5.

```
   Requisição: 05 06 00 64 00 C8 09 50
   Resposta:   05 06 00 64 00 C8 09 50   ← idêntica
```

### 6.4.4 FC16 — Write Multiple Holding Registers

**Requisição:**

```
   ┌──────┬──────┬────────────┬────────────┬──────────┬─────────────┬──────┐
   │ Slv  │ 0x10 │ Start Addr │ Qty regs   │ Byte cnt │ Reg values  │ CRC  │
   │ 1B   │ 1B   │  2B (MSB)  │  2B (MSB)  │   1B     │ 2×Qty bytes │ 2B   │
   └──────┴──────┴────────────┴────────────┴──────────┴─────────────┴──────┘
```

**Resposta (curta):**

```
   ┌──────┬──────┬────────────┬────────────┬──────┐
   │ Slv  │ 0x10 │ Start Addr │ Qty regs   │ CRC  │
   │ 1B   │ 1B   │  2B (MSB)  │  2B (MSB)  │ 2B   │
   └──────┴──────┴────────────┴────────────┴──────┘
```

**Exemplo:** Escrever dois registradores (107 = 0x4382, 108 = 0x0000) — Over-Voltage Threshold = 260.0 V em FLOAT32 — no escravo 5.

**Requisição:**
```
   05  10  00 6B  00 02  04  43 82  00 00  XX XX
   ↑   ↑   ↑      ↑      ↑   ↑      ↑      ↑
   │   │   │      │      │   │      │      └── CRC
   │   │   │      │      │   │      └───────── Reg 108 = 0x0000
   │   │   │      │      │   └──────────────── Reg 107 = 0x4382
   │   │   │      │      └──────────────────── Byte count: 4
   │   │   │      └─────────────────────────── Qty regs: 2
   │   │   └────────────────────────────────── Start addr: 107
   │   └────────────────────────────────────── FC: 0x10 (= 16 decimal)
   └────────────────────────────────────────── Endereço escravo: 5
```

---

## 6.5 Códigos de Exceção

Quando o escravo **não consegue atender** à requisição, ele responde com um **frame de exceção**:

```
   ┌──────┬──────────┬────────────┬──────┐
   │ Slv  │ FC|0x80  │ Excep code │ CRC  │
   │ 1B   │   1B     │    1B      │ 2B   │
   └──────┴──────────┴────────────┴──────┘
```

> **O bit 7 da function code é ligado** para sinalizar erro. Exemplo: FC03 → 0x83; FC16 → 0x90.

| Código | Significado                                            | Quando ocorre                          |
|--------|--------------------------------------------------------|----------------------------------------|
| 0x01   | Illegal Function                                       | Função não suportada pelo escravo      |
| 0x02   | Illegal Data Address                                   | Endereço fora da área válida           |
| 0x03   | Illegal Data Value                                     | Valor não aceitável (ex.: qty = 0)     |
| 0x04   | Server Device Failure                                  | Erro interno do escravo                |
| 0x06   | Server Device Busy                                     | Processamento em andamento, tente depois |

**Exemplo:** Mestre pede FC03, endereço 999 num escravo que só tem 100 registradores. Resposta:

```
   05  83  02  C0 F1
   ↑   ↑   ↑   ↑
   │   │   │   └── CRC
   │   │   └────── Exception code: 0x02 (Illegal Data Address)
   │   └────────── FC original (0x03) | 0x80 = 0x83
   └────────────── Endereço escravo
```

---

## 6.6 O CRC-16 do Modbus

O **CRC-16-MODBUS** é um checksum de 16 bits que detecta corrupção do frame. Usa o polinômio:

$$P(x) = x^{16} + x^{15} + x^2 + 1 \quad \text{(representação binária: 0x8005)}$$

Mas no Modbus, usa-se a **forma refletida**:

$$0\text{xA001}$$

E o valor inicial é **0xFFFF** (todos os bits ligados).

### 6.6.1 Algoritmo passo a passo

```
   1. CRC ← 0xFFFF
   2. Para cada byte do frame (exceto o CRC final):
      a. CRC ← CRC XOR byte
      b. Para cada um dos 8 bits:
         se bit menos significativo de CRC é 1:
            CRC ← (CRC >> 1) XOR 0xA001
         senão:
            CRC ← CRC >> 1
   3. O CRC final é o resultado.
   4. Transmita LSB primeiro, MSB depois.
```

### 6.6.2 Implementação em Python

```python
def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

# Uso:
frame = bytes([0x05, 0x03, 0x00, 0x64, 0x00, 0x02])
crc = crc16_modbus(frame)
# crc = 0x8C4D
# Transmita: 4D 8C (LSB primeiro!)
```

### 6.6.3 Implementação em C

```c
uint16_t crc16_modbus(const uint8_t *data, size_t len) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (int b = 0; b < 8; b++) {
            if (crc & 0x0001) {
                crc = (crc >> 1) ^ 0xA001;
            } else {
                crc >>= 1;
            }
        }
    }
    return crc;
}
```

### 6.6.4 Exemplo numérico — cálculo manual

Vamos calcular o CRC para a requisição **05 03 00 64 00 02**.

Início: `CRC = 0xFFFF`.

**Byte 0x05:**
- `CRC = 0xFFFF XOR 0x0005 = 0xFFFA`
- Bit 0 do CRC = 0 → shift: `0x7FFD`
- Bit 0 = 1 → shift+XOR: `(0x3FFE) XOR 0xA001 = 0x9FFF`
- ... (8 iterações no total)

Para fins didáticos, **rode o código Python** acima — fazer 8 iterações × 6 bytes à mão consome 15 minutos e não acrescenta entendimento conceitual.

O resultado final é **0x8C4D**, transmitido como **`4D 8C`**.

---

## 6.7 Tabela de Lookup (Otimização)

Em microcontroladores, processar o CRC bit-a-bit é lento. A otimização clássica é uma **tabela pré-calculada** de 256 entradas:

```c
static const uint16_t crc_table[256] = { 0x0000, 0xC0C1, 0xC181, ... };

uint16_t crc16_fast(const uint8_t *data, size_t len) {
    uint16_t crc = 0xFFFF;
    while (len--) {
        crc = (crc >> 8) ^ crc_table[(crc & 0xFF) ^ *data++];
    }
    return crc;
}
```

Custo: 512 bytes de Flash. Ganho: processamento ~8× mais rápido.

---

## 6.8 Transação Completa: Um Exemplo Anotado

Vamos seguir uma transação real, **passo a passo**:

### Cenário

- Mestre: PC com EasyModbus
- Escravo: medidor de energia, endereço 1
- Tarefa: ler **Voltage L1-N**, registrador 0–1 (Input Registers, FLOAT32 ABCD)

### Requisição (mestre → escravo)

```
   01  04  00 00  00 02  71 CB
```

| Byte         | Valor | Interpretação                              |
|--------------|-------|--------------------------------------------|
| Slave Addr   | 0x01  | Escravo de endereço 1                      |
| Function     | 0x04  | Read Input Registers                       |
| Start addr H | 0x00  | Endereço inicial (high byte) = 0           |
| Start addr L | 0x00  | Endereço inicial (low byte)                |
| Qty regs H   | 0x00  | Quantidade (high) = 0                      |
| Qty regs L   | 0x02  | Quantidade (low) = 2 (dois registradores)  |
| CRC LSB      | 0x71  | CRC do frame (byte baixo primeiro)         |
| CRC MSB      | 0xCB  | CRC byte alto                              |

### Resposta (escravo → mestre)

Suponha que a tensão é 224.0 V = 0x43600000 em IEEE 754.

```
   01  04  04  43 60  00 00  D3 9F
```

| Byte         | Valor  | Interpretação                              |
|--------------|--------|--------------------------------------------|
| Slave Addr   | 0x01   | Eco do endereço                            |
| Function     | 0x04   | Eco da FC                                  |
| Byte count   | 0x04   | 4 bytes de dados a seguir                  |
| Reg 0 H      | 0x43   | High word do float, byte alto              |
| Reg 0 L      | 0x60   | High word do float, byte baixo             |
| Reg 1 H      | 0x00   | Low word do float, byte alto               |
| Reg 1 L      | 0x00   | Low word do float, byte baixo              |
| CRC LSB      | 0xD3   | CRC                                        |
| CRC MSB      | 0x9F   |                                            |

### Decodificação do FLOAT32

```
   Reg 0 = 0x4360
   Reg 1 = 0x0000

   Concatenação (ABCD): 0x43600000

   IEEE 754:
     S = 0          (positivo)
     E = 10000110   (= 134, expoente = 134 − 127 = 7)
     M = 11000000000000000000000   (mantissa fracionária)

     Valor = (-1)^S × (1 + M) × 2^E
           = 1 × 1,75 × 128
           = 224.0  ✓
```

---

## 6.9 Diagnóstico de Problemas em Redes Modbus RTU

| Sintoma                                        | Causas prováveis                                     |
|------------------------------------------------|------------------------------------------------------|
| Nenhuma resposta                               | Endereço errado; baud/paridade diferentes; cabo solto |
| Resposta com endereço diferente                | Dois escravos com mesmo endereço; mestre confuso     |
| CRC error em todas as transações               | Polaridade A/B trocada; baud rate incorreto          |
| Funciona em curta distância, falha longe       | Sem terminador; sem bias                             |
| Funciona com 1 escravo, falha com 5            | Capacitância da linha (cabos longos); baud rate alto |
| Erros intermitentes após silêncio              | Sem polarização (bias)                               |
| Funciona em PC1, não em PC2                    | Driver USB-RS485 antigo; timing                      |
| Modbus exception 0x02                          | Endereço inexistente — verificar mapa do equipamento |
| Modbus exception 0x03                          | Quantidade inválida (0, > 125, ou intervalo inválido)|

---

## 6.10 Limites Práticos do Modbus RTU

- **Endereços por escravo:** até 247 (1 a 247) — limite do byte de endereço (descontando 0 = broadcast e 248+ reservados)
- **Registradores lidos por requisição:** até 125 (limite imposto pelo tamanho máximo do frame de 256 bytes)
- **Coils lidos por requisição:** até 2000 (cada coil ocupa apenas 1 bit no payload)
- **Escravos por rede:** elétrico do RS-485 (32 cargas-padrão); pode-se chegar a centenas com repetidores
- **Distância:** 1200 m a 9600 baud, menos em taxas maiores
- **Tempo de varredura:** varia com baud rate e tamanho da rede

---

## 6.11 Roteiro do Laboratório 6.1 — Modbus RTU com Simulador

### Material

- 1 PC com **ModbusDeviceSIM** (em modo serial, via com0com)
- 1 PC com **EasyModbus** (ou pymodbus em script)
- Par de portas COM virtuais (com0com: COM10 ↔ COM11)

### Procedimento

1. Configurar com0com criando o par COM10 ↔ COM11.
2. No ModbusDeviceSIM, configurar Modbus RTU em **COM10**, 9600 baud, 8E1, escravo 1, MK-EM3P.
3. No EasyModbus, conectar em **COM11**, mesma configuração.
4. **Ler** registradores 0–91 com **FC04**.
5. **Capturar o tráfego** com um sniffer serial (PortMon, RealTerm) e identificar:
   - O endereço inicial transmitido
   - O CRC
   - A resposta
6. **Calcular manualmente** o CRC de uma requisição e comparar com o capturado.
7. **Escrever** o registrador 100 (CT Primary) com valor 200 usando **FC06**.
8. **Provocar exceção:** ler endereço 9999. Capturar a resposta de erro e identificar o código de exceção.

---

## 6.12 Exercícios

### Cálculos

1. Calcule (a mão ou em código) o CRC-16 do frame **01 04 00 00 00 02**.
2. Identifique o erro: o frame **01 06 00 64 00 C8 09 51** foi recebido. O valor 09 51 é o CRC esperado?
3. Para 9600 baud, 8E1, qual a duração de t3.5 (em ms)?

### Construção de frames

4. Construa o frame Modbus RTU completo para:
   - Ler 10 holding registers a partir do endereço 40, do escravo 7.
   - Escrever o valor 0x55AA no coil 5 do escravo 12.
   - Escrever os valores [0x1234, 0x5678] nos registradores 100 e 101 do escravo 3.
5. Construa a resposta esperada para cada caso acima, supondo valores arbitrários de registradores (você escolhe).

### Interpretação

6. Você capturou o frame: **0A  83  02  C1 60**. Interprete byte a byte. Que comando o mestre tinha tentado? Que erro o escravo retornou?
7. Você vê dois frames consecutivos no fio:
   ```
   01 03 00 00 00 0A C5 CD
   01 03 14 ... (sequência de bytes) ... AA BB
   ```
   Identifique: qual é a requisição, qual é a resposta, e quantos registradores estão sendo lidos?

### Diagnóstico

8. Uma rede Modbus RTU em 9600 baud, 8E1 funciona com 5 escravos. Você adiciona o sexto e ele responde com **CRC error** em algumas transações. Liste 3 hipóteses possíveis e como investigar cada uma.
9. Um operador relata que, após desligar e religar o sistema, o **primeiro frame após o boot** falha sempre, mas os demais funcionam. Diagnóstico provável?

### Projeto

10. **Em laboratório (com pymodbus):**
    - Escreva um script Python que **leia** registradores 0–5 de um escravo Modbus RTU.
    - Faça o script imprimir os bytes brutos enviados e recebidos.
    - Compare com a estrutura teórica vista neste módulo.

---

## 6.13 Síntese

- Frame Modbus RTU: **Slave | FC | Data | CRC** delimitado por **silêncio 3,5T**.
- **CRC-16 Modbus** com polinômio refletido **0xA001**, inicial **0xFFFF**, transmitido **LSB primeiro**.
- **Função codes**: FC03 (R holding), FC04 (R input), FC06 (W single), FC16 (W multiple).
- **Exceções**: FC original | 0x80, com código 0x01–0x0B.
- **Tipos compostos** (FLOAT32, INT32) ocupam **2 registradores consecutivos**, atenção ao byte order.

---

**Próximo módulo:** [07-modbus-ascii.md](07-modbus-ascii.md)
