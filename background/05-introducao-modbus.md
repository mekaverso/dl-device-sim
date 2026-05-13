# Módulo 5 — Introdução ao Protocolo Modbus

> *"Tudo que é simples, sobrevive. O Modbus é a prova viva disso."*

## Objetivos de aprendizagem

Ao final deste módulo, o aluno será capaz de:

1. Narrar o contexto histórico do surgimento do Modbus.
2. Descrever a filosofia mestre-escravo (e a equivalente cliente-servidor).
3. Listar e diferenciar os **4 tipos de dados** do modelo Modbus.
4. Compreender o endereçamento de registradores e a confusão histórica entre 0-based e 1-based.
5. Distinguir os três modos de transmissão: **RTU**, **ASCII** e **TCP**.

---

## 5.1 Contexto Histórico

Em **1968**, a **Modicon** (hoje parte do grupo Schneider Electric) lançou o **primeiro CLP da história**, o **Modicon 084**, em resposta a uma especificação técnica da General Motors. Era uma revolução: até então, controle industrial era feito com **relés eletromecânicos**.

A General Motors queria substituir centenas de relés por **um único dispositivo programável** que pudesse ser reconfigurado por software, em vez de refiação. O 084 foi a resposta.

Mas surgiu logo um novo problema: **como conectar esses CLPs a sistemas supervisórios e a outros equipamentos**?

Cada fabricante criava seu próprio protocolo proprietário — uma babel digital. A Modicon, em **1979**, tomou uma decisão que mudaria a história da automação: **publicar abertamente** seu protocolo serial, batizado de **Modbus**.

> **Por que o nome "Modbus"?**
> **Mod**icon **Bus** = barramento da Modicon. Originalmente era nome de produto; virou padrão *de facto* da indústria.

A especificação foi disponibilizada **livre de royalties**, em uma época em que isso era radical. Resultado: outros fabricantes adotaram massivamente, e o Modbus virou o "esperanto" da automação industrial.

### 5.1.1 Linha do tempo do Modbus

| Ano   | Marco                                                              |
|-------|--------------------------------------------------------------------|
| 1979  | Modbus original (serial, RTU e ASCII)                              |
| 1996  | Modbus TCP introduzido por Schneider                               |
| 2002  | Especificação consolidada como **Modbus Application Protocol V1.1**|
| 2004  | Criação da **Modbus Organization** (consórcio independente)        |
| 2006  | Modbus over Serial Line V1.02 (formalização do RTU/ASCII)          |
| 2007  | Modbus Plus descontinuado (variante proprietária mais rápida)      |
| 2018  | **Modbus/TCP Security** (criptografia TLS)                         |
| 2026  | Continua sendo o protocolo industrial **mais utilizado no mundo**  |

---

## 5.2 Filosofia: Simplicidade Acima de Tudo

A genialidade do Modbus está em **três decisões de projeto**:

### 5.2.1 Mestre-escravo (master-slave)

Em qualquer instante, **um único dispositivo** (o **mestre**) controla a comunicação. Os demais (os **escravos**) só falam quando o mestre lhes pergunta.

```
                  Mestre
                  ┌────┐
                  │ Mq │
                  └────┘
                     ↓ "Escravo 5, dê-me sua temperatura"
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Escravo1 │ │ Escravo5 │ │ EscravoN │
        └──────────┘ └──────────┘ └──────────┘
                          ↑
                          "Sim, é 47.2 °C"
```

**Consequências:**
- **Sem colisões** — o mestre coordena tudo.
- **Comportamento previsível** — o mestre conhece a "ordem da varredura".
- **Limitação**: se o mestre falha, a rede para. (Sem failover automático na especificação básica.)

> **Importante:** Em **Modbus TCP**, fala-se em **cliente** (= mestre) e **servidor** (= escravo). A terminologia mudou para alinhar com o vocabulário de redes IP, mas o conceito é o mesmo.

### 5.2.2 Sem estado

Modbus é **stateless**: cada requisição é independente da anterior. Não há "abrir sessão", "negociar parâmetros", "fazer login". O mestre simplesmente pergunta, o escravo responde.

Vantagem: **simplicidade de implementação** — um microcontrolador modesto consegue ser escravo Modbus.
Desvantagem: nenhuma autenticação, criptografia ou segurança nativa.

### 5.2.3 Modelo de dados padronizado

Modbus define **um único modelo abstrato** de dados que serve para qualquer tipo de equipamento: 4 áreas de memória, cada uma com 65.536 endereços possíveis. Veremos abaixo.

---

## 5.3 O Modelo de Dados Modbus

O Modbus organiza a memória do escravo em **quatro áreas distintas**:

| Tipo                   | Largura | Acesso          | Função tradicional         |
|------------------------|---------|------------------|----------------------------|
| **Coil**               | 1 bit   | Leitura/escrita | Saída digital (relé, lâmpada) |
| **Discrete Input**     | 1 bit   | Apenas leitura  | Entrada digital (botão, sensor)|
| **Input Register**     | 16 bits | Apenas leitura  | Medição analógica          |
| **Holding Register**   | 16 bits | Leitura/escrita | Setpoint, parâmetro        |

### 5.3.1 Visualização

```
   ┌───────────────────────────────────────────────────────┐
   │                  Escravo Modbus                        │
   │                                                        │
   │  Coils (1 bit, R/W)         ──► aciona saídas         │
   │  ┌──┬──┬──┬──┬──┬──┬──┬──┐                            │
   │  │ 0│ 1│ 2│ 3│ 4│ 5│ 6│..│                            │
   │  └──┴──┴──┴──┴──┴──┴──┴──┘                            │
   │                                                        │
   │  Discrete Inputs (1 bit, R)  ◄── lê entradas          │
   │  ┌──┬──┬──┬──┬──┬──┬──┬──┐                            │
   │  │ 0│ 1│ 2│ 3│ 4│ 5│ 6│..│                            │
   │  └──┴──┴──┴──┴──┴──┴──┴──┘                            │
   │                                                        │
   │  Input Registers (16 bits, R) ◄── lê medições         │
   │  ┌────────┬────────┬────────┬─────┐                   │
   │  │ 0:24°C │ 1:25%  │ 2:60Hz │ ... │                   │
   │  └────────┴────────┴────────┴─────┘                   │
   │                                                        │
   │  Holding Registers (16 bits, R/W) ──► setpoints       │
   │  ┌────────┬────────┬────────┬─────┐                   │
   │  │ 0:Sp1  │ 1:Sp2  │ 2:Cfg  │ ... │                   │
   │  └────────┴────────┴────────┴─────┘                   │
   │                                                        │
   └───────────────────────────────────────────────────────┘
```

> **Atenção:** as quatro áreas são **independentes**. O endereço 0 de Coils é uma coisa diferente do endereço 0 de Input Registers. **A function code é que diz** em qual área o mestre quer operar.

### 5.3.2 Origem dos nomes (motivação histórica)

- **Coil**: do inglês *coil*, bobina — referência às bobinas de relés industriais.
- **Discrete Input**: entrada "discreta" = binária (0 ou 1).
- **Input Register**: registrador alimentado por **entradas** (medições).
- **Holding Register**: registrador "mantido" — escrito pelo mestre e mantido pelo escravo.

Esses termos refletem uma realidade dos CLPs dos anos 70/80. Hoje, em medidores e inversores, eles são abstrações lógicas — não há **bobinas físicas** atrás dos coils, mas o nome ficou.

### 5.3.3 Para que serve cada um?

| Área              | Exemplo real em um inversor de frequência          |
|-------------------|----------------------------------------------------|
| Coil              | Bit "RUN" (1 = rodar, 0 = parar)                   |
| Discrete Input    | Bit "FAULT" (1 = falha ativa, 0 = OK)              |
| Input Register    | Velocidade atual (RPM)                             |
| Holding Register  | Setpoint de velocidade (RPM)                       |

| Área              | Exemplo em um medidor de energia                   |
|-------------------|----------------------------------------------------|
| Coil              | (Pouco usado)                                      |
| Discrete Input    | Bit "Sobrecorrente"                                |
| Input Register    | Tensão L1-N, corrente, potência                    |
| Holding Register  | Setpoint de relação TC/TP, threshold de alarme     |

---

## 5.4 Endereçamento: A Grande Confusão Histórica

### 5.4.1 Endereço lógico vs. endereço de protocolo

Aqui mora uma fonte clássica de confusão. Há **duas convenções** em uso:

#### Convenção tradicional (legada, "1-based" com prefixo)

| Faixa lógica   | Tipo                | Área Modbus          |
|----------------|---------------------|----------------------|
| 00001 – 09999  | Coils               | Coil                 |
| 10001 – 19999  | Discrete Inputs     | Discrete Input       |
| 30001 – 39999  | Input Registers     | Input Register       |
| 40001 – 49999  | Holding Registers   | Holding Register     |

O **prefixo numérico** (1, 3, 4) indicava implicitamente o tipo. Exemplo: "registrador 40001" significa "holding register 1".

#### Convenção atual (PDU, "0-based" sem prefixo)

A **especificação oficial moderna** (Modbus Application Protocol V1.1) usa endereçamento **0-based** dentro de cada área:

| Faixa de protocolo | Tipo                | Função code usada |
|--------------------|---------------------|-------------------|
| 0 – 65535          | Coils               | FC01, FC05, FC15  |
| 0 – 65535          | Discrete Inputs     | FC02              |
| 0 – 65535          | Input Registers     | FC04              |
| 0 – 65535          | Holding Registers   | FC03, FC06, FC16  |

A **function code** indica a área; o endereço é apenas o offset dentro dela, contado a partir de **zero**.

### 5.4.2 Tradução entre as duas

```
   Endereço tradicional   Tipo               Endereço protocolo (0-based)
   ──────────────────────────────────────────────────────────────────────
   40001                  Holding Register   0   (porque 40001 − 40001 = 0)
   40002                  Holding Register   1
   40100                  Holding Register   99
   30001                  Input Register     0
   00001                  Coil               0
```

> **Regra prática:** subtraia 1 e ignore o prefixo.
>
> Exemplo: "leia o registrador **40117**" → "leia o **holding register de endereço 116**, usando FC03".

### 5.4.3 Em ModbusDeviceSIM

No nosso simulador, os endereços documentados são **0-based** (PDU). Isso significa que, quando você lê o registrador de tensão L1-N do MK-EM3P:

- Endereço PDU: **0**
- Endereço tradicional: **30001** (input register, FC04)

Verifique sempre a convenção usada pela ferramenta cliente:
- **EasyModbusTCP**: usa 0-based (PDU). Compatível diretamente com nossa documentação.
- **Alguns SCADAs**: usam tradicional (40001, 30001…). Subtraia 1 e ignore o prefixo.

---

## 5.5 Os Três Modos de Transmissão

A especificação Modbus define **três variantes** que diferem **na camada física e no formato do frame**, mas compartilham **o mesmo modelo de dados e as mesmas function codes**:

### 5.5.1 Modbus RTU

- **Camada física:** serial (RS-485 ou RS-232)
- **Codificação:** binária — cada byte transmitido é literalmente um byte do frame
- **Delimitador:** silêncio de **3,5 caracteres** entre frames
- **Verificação:** CRC-16 ao final
- **Eficiência:** **alta** (binário compacto)
- **Uso típico:** redes de campo

### 5.5.2 Modbus ASCII

- **Camada física:** serial
- **Codificação:** texto — cada byte é convertido em **dois caracteres ASCII hexadecimais**. Ex.: byte 0xB4 vira "B" "4".
- **Delimitador:** caracteres `:` (início) e CR/LF (fim)
- **Verificação:** LRC ao final
- **Eficiência:** **metade** do RTU (precisa de 2 caracteres por byte)
- **Uso típico:** legados, links com problemas onde texto ajuda diagnóstico

### 5.5.3 Modbus TCP

- **Camada física:** Ethernet (IP/TCP)
- **Codificação:** binária — semelhante ao RTU mas **sem CRC** (o próprio TCP garante integridade)
- **Cabeçalho adicional:** **MBAP** (Modbus Application Protocol header) — 7 bytes contendo transaction ID, protocol ID, length, unit ID
- **Porta:** 502 (padrão)
- **Eficiência:** **excelente** em redes Ethernet
- **Uso típico:** integração industrial moderna

### 5.5.4 Tabela comparativa

| Aspecto              | RTU              | ASCII             | TCP              |
|----------------------|------------------|-------------------|------------------|
| Camada física        | RS-485/RS-232    | RS-485/RS-232     | Ethernet         |
| Codificação          | Binária          | Texto ASCII Hex   | Binária          |
| Delimitação          | Silêncio 3,5T    | `:` e CR/LF       | Header MBAP      |
| Verificação          | CRC-16           | LRC               | TCP+IP (sem CRC) |
| Bytes por registrador| 2                | 4                 | 2                |
| Múltiplos masters    | **Não**          | Não               | **Sim**          |
| Distância prática    | até 1200 m       | até 1200 m        | LAN inteira      |
| Velocidade           | até ~115 kbps    | até ~115 kbps     | 10 Mbps+         |
| Aplicação            | Campo industrial | Legados           | Supervisão moderna |

---

## 5.6 Function Codes — Um Pequeno Catálogo

A **function code** é um número de 1 byte que diz **o que** o mestre quer fazer. Aqui está o catálogo essencial:

### 5.6.1 Leitura

| FC | Hex  | Operação                       |
|----|------|--------------------------------|
| 01 | 0x01 | Read Coils                     |
| 02 | 0x02 | Read Discrete Inputs           |
| 03 | 0x03 | **Read Holding Registers**     |
| 04 | 0x04 | **Read Input Registers**       |

### 5.6.2 Escrita

| FC | Hex  | Operação                       |
|----|------|--------------------------------|
| 05 | 0x05 | Write Single Coil              |
| 06 | 0x06 | **Write Single Holding Register** |
| 15 | 0x0F | Write Multiple Coils           |
| 16 | 0x10 | **Write Multiple Holding Registers** |

### 5.6.3 Avançadas

| FC | Hex  | Operação                                |
|----|------|----------------------------------------|
| 07 | 0x07 | Read Exception Status (legado)         |
| 08 | 0x08 | Diagnostics                            |
| 17 | 0x11 | Report Slave ID                        |
| 20 | 0x14 | Read File Record                       |
| 21 | 0x15 | Write File Record                      |
| 22 | 0x16 | Mask Write Register                    |
| 23 | 0x17 | Read/Write Multiple Registers          |
| 24 | 0x18 | Read FIFO Queue                        |
| 43 | 0x2B | Encapsulated Interface Transport       |

> **Para esta disciplina** vamos focar em **FC01, FC02, FC03, FC04, FC05, FC06, FC15 e FC16** — cobrem 99 % dos casos reais.

### 5.6.4 Códigos de exceção (na resposta)

Se algo der errado, o escravo responde com a **function code original + 0x80** (bit 7 ligado) e um **código de exceção**:

| Código | Significado                                       |
|--------|---------------------------------------------------|
| 0x01   | Illegal Function (FC não suportada)              |
| 0x02   | Illegal Data Address (endereço fora de faixa)    |
| 0x03   | Illegal Data Value                                |
| 0x04   | Server (Slave) Device Failure                    |
| 0x05   | Acknowledge                                       |
| 0x06   | Server Device Busy                                |
| 0x08   | Memory Parity Error                               |
| 0x0A   | Gateway Path Unavailable                          |
| 0x0B   | Gateway Target Device Failed to Respond           |

Veremos códigos de exceção em ação no próximo módulo.

---

## 5.7 Um Frame em Pseudo-código (Apresentação)

Veremos no Módulo 6 (Modbus RTU) e Módulo 9 (Modbus TCP) os frames em detalhes byte a byte. Para introduzir, considere a estrutura **lógica** de qualquer transação Modbus:

```
   ┌────────────────────────────────┐
   │ Endereço do escravo (1 byte)   │  ← em Modbus RTU; no TCP é um campo "Unit ID"
   ├────────────────────────────────┤
   │ Function Code (1 byte)         │
   ├────────────────────────────────┤
   │ Dados específicos da função    │
   │ (varia: endereço inicial,      │
   │  quantidade, valores…)         │
   ├────────────────────────────────┤
   │ Verificação (CRC, LRC, ou ø)   │
   └────────────────────────────────┘
```

E a **resposta** é estruturada de forma simétrica.

---

## 5.8 Tipos de Dados — Como Codificar um FLOAT no Modbus?

O Modbus base usa **registradores de 16 bits** como unidade fundamental. Mas a maioria das medições industriais (tensão, corrente, temperatura) precisa de mais precisão.

**A convenção mais comum** é codificar números reais como **IEEE 754 FLOAT32**, ocupando **2 registradores** consecutivos (32 bits).

### 5.8.1 Ordem dos bytes — a "guerra" do byte order

Há **quatro maneiras** populares de organizar os 4 bytes de um float em 2 registradores:

```
   FLOAT 224.0 = 0x43600000 (IEEE 754)
   Bytes: B3 = 0x43 (MSB)
          B2 = 0x60
          B1 = 0x00
          B0 = 0x00 (LSB)
```

| Ordem (notação)    | Registrador 1 | Registrador 2 | Equipamentos típicos        |
|--------------------|---------------|---------------|-----------------------------|
| **ABCD** (big-endian)    | 0x4360        | 0x0000        | Schneider, padrão "ortodoxo"|
| BADC               | 0x6043        | 0x0000        | Alguns Siemens              |
| **CDAB** (word-swap)     | 0x0000        | 0x4360        | Muitos medidores chineses   |
| **DCBA** (little-endian) | 0x0000        | 0x6043        | Alguns drivers              |

> **No ModbusDeviceSIM**, usamos **ABCD (big-endian)**. Quando um cliente lê o registrador 0 e 1, recebe:
> - Reg 0 = 0x4360 (high word)
> - Reg 1 = 0x0000 (low word)
> Combinados em ordem ABCD = 0x43600000 = 224.0 V.

### 5.8.2 Outros tipos compostos

- **INT32 / UINT32**: 2 registradores (4 bytes), idem byte order
- **INT64 / UINT64**: 4 registradores
- **STRING**: cada registrador carrega 2 caracteres ASCII (alguns fabricantes usam ordem invertida)
- **BIT FIELDS**: 16 flags individuais em um registrador (usados para status/alarme)

---

## 5.9 Síntese — Os 7 conceitos do Modbus que você precisa saber

1. **Mestre-escravo** (ou cliente-servidor em TCP)
2. **Modelo de 4 áreas**: Coils, Discrete Inputs, Input Registers, Holding Registers
3. **Function codes** identificam **a operação** e implicitamente **a área**
4. **Endereço** identifica **a posição** dentro da área
5. **RTU/ASCII/TCP**: três variantes de transmissão, mesmo modelo lógico
6. **CRC/LRC** (serial) ou **TCP** (Ethernet) garantem integridade
7. **FLOAT32** = 2 registradores com convenção de byte order

---

## 5.10 Exercícios

### Conceituais

1. Por que o Modbus se tornou um padrão *de facto* mesmo sem ser oficialmente adotado por um órgão internacional como ISO ou IEEE?
2. Diferencie **mestre/escravo** (Modbus serial) de **cliente/servidor** (Modbus TCP). É a mesma coisa? Em que sentido?
3. Por que o modelo de dados Modbus usa **4 áreas separadas** em vez de uma única memória contígua?

### Análise

4. Um equipamento documenta seus registradores começando em **30001**. Que tipo de dado são esses registradores? Qual function code o mestre deve usar? E qual é o endereço **PDU** correspondente?
5. Um medidor reporta a tensão em FLOAT32 no endereço 0-1 (PDU). Você lê e recebe `(0x6043, 0x0000)`. Qual é a tensão **assumindo ordem ABCD**? E **assumindo CDAB**? Justifique a diferença.

### Aplicação

6. Em um inversor de frequência:
   - O bit RUN (1 = rodar) precisa ser **escrito** pelo CLP. Em qual área Modbus deveria estar? Justifique.
   - O bit FAULT (1 = falha) só é **lido** pelo CLP, nunca escrito. Em qual área? Justifique.
   - A frequência de saída atual (Hz) é **lida** pelo CLP. Em qual área?
   - O setpoint de frequência é **escrito** pelo CLP. Em qual área?
7. **Pesquisa.** Procure o manual de um medidor de energia (qualquer marca) e identifique:
   - O endereçamento usado (tradicional ou PDU)
   - A convenção de byte order para FLOAT32
   - O endereço da Tensão L1-N

### Síntese

8. Por que a Modbus Organization define **as mesmas function codes** para RTU, ASCII e TCP? Que vantagem isso traz para desenvolvedores e usuários?
9. Crie uma tabela mental: para cada uma das seguintes operações, qual função code você usaria?
   - Acender uma saída digital
   - Ler 10 temperaturas
   - Configurar 5 parâmetros do equipamento
   - Verificar status de uma entrada digital
   - Ler 4 medidas de corrente
10. **Reflexão.** Se você fosse projetar um protocolo industrial em 2026, manteria a divisão em 4 áreas de dados? O que mudaria? Justifique sua resposta considerando uma perspectiva crítica.

---

## 5.11 Leitura recomendada para o próximo módulo

- **Modbus Organization** — *Modbus Application Protocol V1.1b3*, seções 1, 2, 6.1–6.6
- Revisar:
  - Aritmética binária e hexadecimal
  - Operações bit a bit (AND, OR, XOR, shift)
  - O conceito de **CRC** (Cyclic Redundancy Check)
  - Polinômio geradores em GF(2)

---

**Próximo módulo:** [06-modbus-rtu.md](06-modbus-rtu.md)
