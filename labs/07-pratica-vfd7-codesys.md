# Prática 7 — MK-VFD7 com CODESYS (WebVisu)

> *"O CLP não fica esperando um operador — ele decide, executa e registra, mesmo de madrugada."*

---

## 1. Contexto Industrial

Em uma planta industrial real, inversores de frequência raramente são controlados manualmente. Eles recebem comandos de um **CLP (Controlador Lógico Programável)** que executa sequências automáticas: parte uma bomba quando o nível do tanque cai, inverte o sentido de uma esteira quando um sensor detecta obstáculo, ajusta a velocidade de um ventilador conforme a temperatura.

O **CODESYS Development System** é um ambiente de programação CLP amplamente usado em automação industrial. Ele permite programar em **Structured Text (ST)**, Ladder, FBD, entre outras linguagens, e disponibiliza uma **WebVisu** — uma interface web de supervisão que roda diretamente no runtime do CLP e pode ser acessada de qualquer navegador na rede.

Nesta prática, você vai:

- Adicionar controle de inversor ao projeto CODESYS já desenvolvido na **Prática Lab 03** (EM3P).
- Criar um segundo Modbus TCP Slave (VFD7) sob o mesmo master.
- Implementar em ST a **lógica de controle** (start/stop/reverse, referência de frequência).
- Construir um **painel WebVisu** com botões de controle, slider de frequência e tendência em tempo real.

A mesma estrutura que você montará aqui é usada em CLPs Wago, Beckhoff, Pilz, Bosch Rexroth e outros fabricantes que rodam CODESYS.

---

## 2. Conceitos Necessários

### 2.1 Control Word — A Linguagem dos Inversores

Praticamente todo inversor industrial — WEG, ABB, Siemens, Danfoss, Schneider — usa um registrador chamado **Control Word** (Palavra de Controle). É um UINT16 onde **cada bit é um comando**:

| Valor | Significado        |
|-------|--------------------|
| `0`   | STOP               |
| `1`   | RUN FORWARD (bit 0)|
| `3`   | RUN REVERSE (bits 0+1) |

No MK-VFD7, a Control Word está no **Holding Register 100** (FC03/FC06).

> **Por que usar bits em vez de campos separados?** Um único registrador Modbus transporta 16 bits. Usar bitmask permite enviar múltiplos comandos simultaneamente em uma única transação — eficiência de rede.

Você já viu este conceito na **Prática Lab 06** (VFD7 com EasyModbusTCP). Aqui, em vez de digitá-lo manualmente, o CLP vai calculá-lo automaticamente a partir de variáveis BOOL.

### 2.2 Drive Status Word — Feedback do Inversor

O registrador de status está no **Input Register 26** (FC04, UINT16):

| Bit | Máscara  | Significado   |
|-----|----------|---------------|
| 0   | `0x0001` | Running       |
| 1   | `0x0002` | Forward       |
| 2   | `0x0004` | Reverse       |
| 3   | `0x0008` | At Reference  |

Para extrair um bit específico em ST, use o operador `AND`:

```iecst
bRunning   := (wDriveStatus AND 16#0001) <> 0;
bForward   := (wDriveStatus AND 16#0002) <> 0;
bAtRef     := (wDriveStatus AND 16#0008) <> 0;
```

### 2.3 FLOAT32: Decodificação e Codificação via UNION

Como você aprendeu no Lab 03, valores FLOAT32 chegam do Modbus como **dois WORDs consecutivos**. Para decodificar, você usa uma UNION que compartilha a memória entre `REAL` e dois `WORD`:

```iecst
TYPE MODBUS_FLOAT32 :
STRUCT
    arWord : ARRAY[0..1] OF WORD;
    rValue : REAL;  (* sobreposto ao arWord *)
END_STRUCT
END_TYPE
```

**Decodificação (leitura — do Modbus para REAL):**
```iecst
// MK-VFD7 usa big-endian ABCD: high word = reg[0], low word = reg[1]
uDec.arWord[1] := wFreq_Hi;   // high word (reg offset 0)
uDec.arWord[0] := wFreq_Lo;   // low word  (reg offset 1)
rOutputFreq    := uDec.rValue;
```

**Codificação (escrita — de REAL para Modbus):**
```iecst
// O caminho inverso: colocar o REAL, extrair os WORDs
uEnc.rValue  := rFreqRef;
wFreqRef_Hi  := uEnc.arWord[1];  // high word → reg 101
wFreqRef_Lo  := uEnc.arWord[0];  // low word  → reg 102
```

> Repassando a lógica: `arWord[1]` é sempre o word mais significativo (bits 31–16) e `arWord[0]` é o menos significativo (bits 15–0). A ordem big-endian do MK-VFD7 coloca o high word **primeiro** na rede, então ele vai para o registrador de menor endereço.

### 2.4 Por que FC06 para Control Word e FC16 para FreqRef?

- **FC06 (Write Single Register):** escreve exatamente **1 registrador** UINT16. Ideal para a Control Word (registrador 100), que é um único UINT16.
- **FC16 (Write Multiple Registers):** escreve **N registradores consecutivos**. Necessário para a Frequency Reference (registradores 101–102), que são dois WORDs formando um FLOAT32.

No CODESYS, você configura canais separados para cada função code de escrita.

### 2.5 Mapa de Registradores do MK-VFD7

> Você já conhece estes registradores do **Lab 06** (EasyModbusTCP). Aqui está a referência completa para a configuração CODESYS.

**Medições — FC04 (Input Registers, FLOAT32 big-endian ABCD):**

| Endereço | Variável         | Tipo    | Unidade |
|----------|------------------|---------|---------|
| 0–1      | Output Frequency | FLOAT32 | Hz      |
| 2–3      | Output Voltage   | FLOAT32 | V       |
| 4–5      | Output Current   | FLOAT32 | A       |
| 6–7      | Output Power     | FLOAT32 | kW      |
| 8–9      | Motor Speed      | FLOAT32 | RPM     |
| 10–11    | Motor Torque     | FLOAT32 | %       |
| 26       | Drive Status     | UINT16  | bitmask |

**Controle e Configuração — FC03/FC06/FC16 (Holding Registers):**

| Endereço | Variável            | Tipo    | Descrição              |
|----------|---------------------|---------|------------------------|
| 100      | Control Word        | UINT16  | 0=STOP, 1=FWD, 3=REV  |
| 101–102  | Frequency Reference | FLOAT32 | Setpoint em Hz         |
| 103–104  | Acceleration Time   | FLOAT32 | Segundos               |
| 105–106  | Deceleration Time   | FLOAT32 | Segundos               |
| 107–108  | Max Frequency       | FLOAT32 | Hz                     |

---

## 3. Material e Setup

### 3.1 Hardware e Software

| Item | Descrição |
|------|-----------|
| Laptop | CODESYS Development System 3.5 instalado |
| Smartphone 1 | ModbusDeviceSIM — modo **MK-EM3P**, porta 5020 (do Lab 03) |
| Smartphone 2 | ModbusDeviceSIM — modo **MK-VFD7**, porta 5020, **modo REMOTE** |
| Rede | Wi-Fi comum — todos na mesma sub-rede |

> **Dois smartphones com IPs diferentes.** O smartphone do EM3P tem um IP (ex.: `192.168.0.105`) e o do VFD7 tem outro (ex.: `192.168.0.107`). Anote ambos antes de começar.

### 3.2 No smartphone do VFD7

1. Abra o **ModbusDeviceSIM**.
2. Selecione **MK-VFD7** no card Device Type.
3. Toque em **START**.
4. **Importante:** Ative o switch **LOCAL → REMOTE** no painel do app. Em modo LOCAL, comandos Modbus via CLP são ignorados.
5. Anote o IP exibido.

### 3.3 Projeto de partida

Esta prática pressupõe que você tem o projeto CODESYS do **Lab 03** (EM3P com WebVisu básica) aberto e funcional. Se não tiver esse projeto:

- Crie um novo projeto CODESYS com Modbus TCP Master e um Slave para o EM3P conforme descrito no Lab 03.
- A estrutura deve ter: `Modbus_TCP_Master` → `Modbus_TCP_Slave_EM3P` com pelo menos os canais de leitura de tensão e potência.

---

## 4. Procedimento

### Parte A — Abrir o Projeto do Lab 03

1. Abra o **CODESYS Development System**.
2. Vá em **File → Open Project** e carregue o projeto salvo na Prática Lab 03.
3. Verifique na árvore de dispositivos (painel esquerdo) que você tem a estrutura:

```
   MyController (CODESYS Control Win V3)
   └── Device
       └── Modbus_TCP_Master
           └── Modbus_TCP_Slave_EM3P   ← do Lab 03
```

4. Execute **Build → Build** (F11). Deve compilar sem erros. Se houver erros, resolva antes de prosseguir.
5. Salve o projeto com **File → Save** (Ctrl+S).

---

### Parte B — Adicionar o Segundo Slave (VFD7)

Como você fez no Lab 03 para adicionar o Slave do EM3P, adicione agora um segundo Slave para o VFD7 **sob o mesmo Modbus_TCP_Master**:

1. Na árvore de dispositivos, clique com o botão direito em **Modbus_TCP_Master**.
2. Selecione **Add Device...**.
3. Na janela de catálogo, expanda **Fieldbuses → Modbus → Modbus TCP Slave**.
4. Clique em **Add Device** e feche.
5. Um novo `Modbus_TCP_Slave` aparece sob o Master. Renomeie-o para `Modbus_TCP_Slave_VFD7`:
   - Clique com o botão direito → **Rename**.
   - Digite `Modbus_TCP_Slave_VFD7` e pressione Enter.

A estrutura agora deve ser:

```
   Modbus_TCP_Master
   ├── Modbus_TCP_Slave_EM3P    ← Lab 03 (existente)
   └── Modbus_TCP_Slave_VFD7   ← novo (Lab 07)
```

---

### Parte C — Configurar o Slave VFD7

1. Dê duplo clique em **Modbus_TCP_Slave_VFD7** para abrir a janela de configuração.
2. Na aba **General**, preencha:

   | Campo           | Valor                    |
   |-----------------|--------------------------|
   | IP Address      | `<IP do smartphone VFD7>`|
   | Port            | `5020`                   |
   | Unit Identifier | `1`                      |

3. Confirme que **Enable** está marcado.
4. Clique em **OK** ou mude para a aba de canais.

> **Atenção:** use o IP do **smartphone do VFD7**, que é diferente do smartphone do EM3P. Não confunda os dois IPs.

---

### Parte D — Configurar os 5 Canais do VFD7

Ainda na configuração do `Modbus_TCP_Slave_VFD7`, vá para a aba **Modbus Slave Channel**. Você criará 5 canais. Para cada um, clique em **Add Channel**.

#### Canal 1 — Medições Analógicas (FC04, leitura)

| Campo             | Valor                        |
|-------------------|------------------------------|
| Name              | `Ch1_Measurements`           |
| Function Code     | `Read Input Registers (FC04)`|
| Offset            | `0`                          |
| Length            | `12`                         |
| Writable          | `NO`                         |

> Este canal lê os registradores 0–11: Output Frequency (0–1), Output Voltage (2–3), Output Current (4–5), Output Power (6–7), Motor Speed (8–9), Motor Torque (10–11). São 12 WORDs = 6 floats.

#### Canal 2 — Drive Status (FC04, leitura)

| Campo             | Valor                        |
|-------------------|------------------------------|
| Name              | `Ch2_DriveStatus`            |
| Function Code     | `Read Input Registers (FC04)`|
| Offset            | `26`                         |
| Length            | `1`                          |
| Writable          | `NO`                         |

> Lê apenas o registrador 26: Drive Status UINT16 (bitmask de estado).

#### Canal 3 — Parâmetros de Configuração (FC03, leitura)

| Campo             | Valor                           |
|-------------------|---------------------------------|
| Name              | `Ch3_Config`                    |
| Function Code     | `Read Holding Registers (FC03)` |
| Offset            | `100`                           |
| Length            | `10`                            |
| Writable          | `NO`                            |

> Lê registradores 100–109: Control Word, FreqRef, Acc Time, Dec Time, Max Freq (para monitoração). Writable = NO — este canal serve apenas para leitura de retorno (readback). Os comandos de escrita usam canais separados (4 e 5).

#### Canal 4 — Escrita da Control Word (FC06, escrita)

| Campo             | Valor                            |
|-------------------|----------------------------------|
| Name              | `Ch4_WriteControlWord`           |
| Function Code     | `Write Single Register (FC06)`   |
| Offset            | `100`                            |
| Length            | `1`                              |
| Writable          | `YES`                            |

> Este canal é mapeado para uma variável `%QW` que representa o registrador 100 (Control Word). Quando o PLC escreve nessa variável, o CODESYS envia um FC06 para o VFD.

#### Canal 5 — Escrita da Frequência de Referência (FC16, escrita)

| Campo             | Valor                               |
|-------------------|-------------------------------------|
| Name              | `Ch5_WriteFreqRef`                  |
| Function Code     | `Write Multiple Registers (FC16)`   |
| Offset            | `101`                               |
| Length            | `2`                                 |
| Writable          | `YES`                               |

> Este canal cobre os registradores 101–102 (FreqRef FLOAT32 = 2 WORDs). Mapeado para dois `%QW` consecutivos.

Após criar os 5 canais, clique em **OK** e salve o projeto.

---

### Parte E — Criar a GVL_VFD7

Agora você precisa das variáveis globais do VFD7. Como você fez com `GVL_EM3P` no Lab 03, crie uma nova GVL:

1. Na árvore do projeto, clique com o botão direito em **Application**.
2. Selecione **Add Object → Global Variable List**.
3. Nomeie como `GVL_VFD7` e clique em **Add**.

Cole o seguinte conteúdo na GVL:

```iecst
VAR_GLOBAL
    (* =========================================================
       GVL_VFD7 — Variáveis Globais do MK-VFD7
       Mekatronik — Advanced Engineering | Lab 07
       ========================================================= *)

    (* --- Registradores brutos — mapeados pelo I/O Mapping --- *)
    (* Canal 1: FC04, offset 0, length 12 — medições analógicas *)
    arMeas     : ARRAY[0..11] OF WORD;   (* %IW — 12 WORDs de medição *)

    (* Canal 2: FC04, offset 26, length 1 — status *)
    wStatus_Raw : WORD;                  (* %IW — Drive Status UINT16 *)

    (* Canal 3: FC03, offset 100, length 10 — config readback *)
    arConfig   : ARRAY[0..9] OF WORD;   (* %IW — 10 WORDs de configuração *)

    (* Canal 4: FC06, offset 100, length 1 — escrita Control Word *)
    wControlWord : WORD;                 (* %QW — Control Word de saída *)

    (* Canal 5: FC16, offset 101, length 2 — escrita FreqRef *)
    wFreqRef_Hi  : WORD;                 (* %QW — high word FreqRef *)
    wFreqRef_Lo  : WORD;                 (* %QW — low word  FreqRef *)

    (* --- Valores decodificados (para leitura fácil no programa) --- *)
    rOutputFreq  : REAL;   (* Hz  *)
    rOutputVolt  : REAL;   (* V   *)
    rOutputCurr  : REAL;   (* A   *)
    rOutputPower : REAL;   (* kW  *)
    rMotorSpeed  : REAL;   (* RPM *)
    rMotorTorque : REAL;   (* %   *)
    wDriveStatus : WORD;   (* bitmask *)

    (* --- Bits decodificados do Status Word --- *)
    bRunning   : BOOL;
    bForward   : BOOL;
    bReverse   : BOOL;
    bAtRef     : BOOL;

    (* --- Variáveis de comando (escritas pela WebVisu) --- *)
    bStartFwd  : BOOL;   (* Botão START FORWARD *)
    bStartRev  : BOOL;   (* Botão START REVERSE *)
    bStop      : BOOL;   (* Botão STOP          *)
    rFreqRef   : REAL;   (* Slider/Input: referência de frequência (Hz) *)

END_VAR
```

Salve o arquivo.

---

### Parte F — I/O Mapping do VFD7

Agora você precisa vincular os canais criados na Parte D às variáveis da GVL_VFD7.

1. Na árvore, dê duplo clique em **Modbus_TCP_Slave_VFD7**.
2. Vá para a aba **Modbus Slave I/O Mapping**.

Você verá cada canal listado. Vincule conforme a tabela abaixo:

| Canal                   | Direção | Variável a vincular         |
|-------------------------|---------|-----------------------------|
| Ch1_Measurements [0]    | %IW     | `GVL_VFD7.arMeas[0]`        |
| Ch1_Measurements [1]    | %IW     | `GVL_VFD7.arMeas[1]`        |
| ...                     | %IW     | *(até arMeas[11])*          |
| Ch2_DriveStatus [0]     | %IW     | `GVL_VFD7.wStatus_Raw`      |
| Ch3_Config [0..9]       | %IW     | `GVL_VFD7.arConfig[0..9]`  |
| Ch4_WriteControlWord[0] | %QW     | `GVL_VFD7.wControlWord`     |
| Ch5_WriteFreqRef [0]    | %QW     | `GVL_VFD7.wFreqRef_Hi`      |
| Ch5_WriteFreqRef [1]    | %QW     | `GVL_VFD7.wFreqRef_Lo`      |

> **Dica prática:** Para o Canal 1 (12 WORDs), no campo de mapeamento você pode digitar `GVL_VFD7.arMeas` e o CODESYS mapeia todo o array automaticamente, se o tamanho coincidir.

Após vincular, clique em **OK** e salve.

---

### Parte G — Lógica em PLC_PRG

Abra o **PLC_PRG** (na árvore: Application → PLC_PRG). Você já tem código do Lab 03 para o EM3P. **Adicione** as seções abaixo **após** o código existente do EM3P — não apague nada que já funciona.

#### G.1 — Declaração de variáveis locais (VAR)

Na seção `VAR` do PLC_PRG, adicione:

```iecst
    (* --- VFD7: UNION para decode/encode FLOAT32 --- *)
    uDec    : MODBUS_FLOAT32;
    uEnc    : MODBUS_FLOAT32;
```

> O tipo `MODBUS_FLOAT32` foi criado no Lab 03. Se não existir no seu projeto, crie um DUT (Data Unit Type) com:
> ```iecst
> TYPE MODBUS_FLOAT32 :
> STRUCT
>     arWord : ARRAY[0..1] OF WORD;
>     rValue : REAL;
> END_STRUCT
> END_TYPE
> ```

#### G.2 — Seção de Decodificação (leitura do VFD7)

Adicione no corpo do PLC_PRG (seção executada a cada ciclo):

```iecst
(* =========================================================
   VFD7 — Decodificação FLOAT32 dos registradores de medição
   Canal 1: arMeas[0..11], big-endian ABCD
   ========================================================= *)

// Output Frequency (regs 0–1)
uDec.arWord[1] := GVL_VFD7.arMeas[0];
uDec.arWord[0] := GVL_VFD7.arMeas[1];
GVL_VFD7.rOutputFreq := uDec.rValue;

// Output Voltage (regs 2–3)
uDec.arWord[1] := GVL_VFD7.arMeas[2];
uDec.arWord[0] := GVL_VFD7.arMeas[3];
GVL_VFD7.rOutputVolt := uDec.rValue;

// Output Current (regs 4–5)
uDec.arWord[1] := GVL_VFD7.arMeas[4];
uDec.arWord[0] := GVL_VFD7.arMeas[5];
GVL_VFD7.rOutputCurr := uDec.rValue;

// Output Power (regs 6–7)
uDec.arWord[1] := GVL_VFD7.arMeas[6];
uDec.arWord[0] := GVL_VFD7.arMeas[7];
GVL_VFD7.rOutputPower := uDec.rValue;

// Motor Speed (regs 8–9)
uDec.arWord[1] := GVL_VFD7.arMeas[8];
uDec.arWord[0] := GVL_VFD7.arMeas[9];
GVL_VFD7.rMotorSpeed := uDec.rValue;

// Motor Torque (regs 10–11)
uDec.arWord[1] := GVL_VFD7.arMeas[10];
uDec.arWord[0] := GVL_VFD7.arMeas[11];
GVL_VFD7.rMotorTorque := uDec.rValue;

(* Drive Status UINT16 — cópia direta *)
GVL_VFD7.wDriveStatus := GVL_VFD7.wStatus_Raw;

(* Decodificar bits do Status Word *)
GVL_VFD7.bRunning := (GVL_VFD7.wDriveStatus AND 16#0001) <> 0;
GVL_VFD7.bForward := (GVL_VFD7.wDriveStatus AND 16#0002) <> 0;
GVL_VFD7.bReverse := (GVL_VFD7.wDriveStatus AND 16#0004) <> 0;
GVL_VFD7.bAtRef   := (GVL_VFD7.wDriveStatus AND 16#0008) <> 0;
```

#### G.3 — Seção de Controle (lógica de comando)

```iecst
(* =========================================================
   VFD7 — Lógica de controle (botões → Control Word)
   bStop, bStartFwd, bStartRev são escritos pela WebVisu
   ========================================================= *)

IF GVL_VFD7.bStop THEN
    GVL_VFD7.wControlWord := 0;     (* STOP *)
    GVL_VFD7.bStop := FALSE;        (* auto-reset do pulso *)
ELSIF GVL_VFD7.bStartFwd THEN
    GVL_VFD7.wControlWord := 1;     (* RUN FORWARD *)
    GVL_VFD7.bStartFwd := FALSE;    (* auto-reset *)
ELSIF GVL_VFD7.bStartRev THEN
    GVL_VFD7.wControlWord := 3;     (* RUN REVERSE *)
    GVL_VFD7.bStartRev := FALSE;    (* auto-reset *)
END_IF
```

> **Por que auto-reset?** A Control Word deve receber um **valor** que fica no registrador — não é um pulso de nível. Se o BOOL ficasse `TRUE` permanentemente, a cada ciclo do CLP ele reenviaria o mesmo comando via FC06, causando tráfego desnecessário. O auto-reset garante que o comando seja enviado uma vez e a variável Modbus reflita o estado atual.

#### G.4 — Seção de Codificação (REAL → WORDs para escrita)

```iecst
(* =========================================================
   VFD7 — Codificação FLOAT32 da referência de frequência
   rFreqRef (REAL, Hz) → wFreqRef_Hi / wFreqRef_Lo (WORD)
   ========================================================= *)

// Limitar rFreqRef a [0.0, 60.0] Hz por segurança
IF GVL_VFD7.rFreqRef < 0.0 THEN
    GVL_VFD7.rFreqRef := 0.0;
ELSIF GVL_VFD7.rFreqRef > 60.0 THEN
    GVL_VFD7.rFreqRef := 60.0;
END_IF

// Encode: REAL → dois WORDs big-endian
uEnc.rValue          := GVL_VFD7.rFreqRef;
GVL_VFD7.wFreqRef_Hi := uEnc.arWord[1];   // high word → reg 101
GVL_VFD7.wFreqRef_Lo := uEnc.arWord[0];   // low word  → reg 102
```

> A limitação de `[0.0, 60.0]` é uma proteção de software: a WebVisu pode deixar o usuário digitar qualquer número; o CLP sanitiza antes de enviar ao inversor.

Após adicionar todas as seções, salve o PLC_PRG.

---

### Parte H — WebVisu: Painel VFD7

Abra a **WebVisu** do seu projeto (Application → Visualization → WebVisu). Você já tem o painel do EM3P do Lab 03. Vamos adicionar um painel VFD7 **ao lado** ou **abaixo** do EM3P, sem remover o que já existe.

#### H.1 — Área do painel VFD7

Desenhe um retângulo de fundo (Rectangle) para delimitar o painel do VFD7. Sugestão: largura 480 px, altura 400 px. Cor de fundo: cinza escuro (`#2A2A2A`) para diferenciar do painel EM3P. Adicione um Text fixo: **"MK-VFD7 — Inversor de Frequência"** no topo do painel.

#### H.2 — Botões de Controle

Adicione três botões (Rectangle ou Button):

**Botão START FWD:**
- Texto: `START FWD`
- Cor de fundo: verde (`#1A7F37`)
- Cor do texto: branco
- Em **Input Configuration → OnMouseDown**:
  - Variable: `GVL_VFD7.bStartFwd`
  - Action: `Write Value = TRUE`

**Botão STOP:**
- Texto: `STOP`
- Cor de fundo: vermelho (`#B22222`)
- Cor do texto: branco
- Em **Input Configuration → OnMouseDown**:
  - Variable: `GVL_VFD7.bStop`
  - Action: `Write Value = TRUE`

**Botão START REV:**
- Texto: `START REV`
- Cor de fundo: laranja (`#E67E00`)
- Cor do texto: branco
- Em **Input Configuration → OnMouseDown**:
  - Variable: `GVL_VFD7.bStartRev`
  - Action: `Write Value = TRUE`

#### H.3 — Slider de Frequência de Referência

Adicione um **Slider** (elemento Linear Slider):
- Variable: `GVL_VFD7.rFreqRef`
- Min: `0.0`, Max: `60.0`
- Orientação: horizontal
- Label: `Freq Ref (Hz)`
- Posicione abaixo dos botões.

#### H.4 — Campo de Entrada Numérica (alternativa ao slider)

Adicione um **Input Field** (Text Field com edição habilitada):
- Variable: `GVL_VFD7.rFreqRef`
- Em **Input Configuration**: habilitado para digitação.
- Formato de exibição: `%.1f Hz`
- Posicione ao lado do slider.

> O slider é conveniente para ajuste rápido; o campo de entrada permite precisão.

#### H.5 — Campos de Exibição (Text Fields read-only)

Adicione campos de texto com as seguintes variáveis e formatos:

| Label                | Variable                  | Formato     |
|----------------------|---------------------------|-------------|
| `Frequência Saída:`  | `GVL_VFD7.rOutputFreq`    | `%.2f Hz`   |
| `Corrente Saída:`    | `GVL_VFD7.rOutputCurr`    | `%.2f A`    |
| `Potência Saída:`    | `GVL_VFD7.rOutputPower`   | `%.3f kW`   |
| `Drive Status:`      | `GVL_VFD7.wDriveStatus`   | `%d (hex)`  |
| `Rodando:`           | `GVL_VFD7.bRunning`       | BOOL (lamp) |
| `Em Referência:`     | `GVL_VFD7.bAtRef`         | BOOL (lamp) |

Para `bRunning` e `bAtRef`, use um elemento **Lamp** (ou Rectangle com cor condicionada): verde quando `TRUE`, cinza quando `FALSE`.

#### H.6 — Tendência em Tempo Real (Trend)

Adicione um elemento **Trend** (gráfico de tendência):
- **Canal 1:** `GVL_VFD7.rOutputFreq` — Label: `Frequência (Hz)`, cor: azul
- **Janela de tempo:** 60 segundos
- **Escala Y:** 0 a 65 Hz
- Posicione na parte inferior do painel VFD7.

> A tendência permite observar visualmente a **rampa de aceleração** (frequência subindo da partida até o setpoint) e a **rampa de desaceleração** (ao parar). Isso é equivalente a um recorder de processo.

#### H.7 — Salvar a WebVisu

Salve a WebVisu. Faça Build do projeto (F11). Corrija eventuais erros de variável ou mapeamento.

---

### Parte H (continuação) — Verificação antes do download

Antes de fazer o download para o runtime:

1. Confira na árvore que os dois slaves estão configurados com os IPs corretos.
2. Abra o **PLC_PRG** e verifique que o código compila sem erros (Build).
3. Abra o **I/O Mapping** do `Modbus_TCP_Slave_VFD7` e certifique-se de que todos os canais estão vinculados a variáveis (nenhuma linha com endereço em branco).

> **ATENÇÃO:** Um mapeamento incompleto não gera erro de compilação — o CODESYS simplesmente não envia/recebe aquele registrador. Se wControlWord não estiver mapeada, os comandos de controle não chegarão ao drive.

---

### Parte I — Download e Teste

#### I.1 — Fazer o Download

1. No CODESYS, vá em **Online → Login** (Alt+F8). Se pedir, selecione o runtime local.
2. Clique em **Download** (F8) para transferir o projeto ao runtime.
3. Inicie a execução: **Debug → Start** (F5).

#### I.2 — Verificar comunicação com o VFD7

1. Abra o **Watch Window** (Debug → Watch). Adicione as variáveis:
   - `GVL_VFD7.rOutputFreq`
   - `GVL_VFD7.wDriveStatus`
   - `GVL_VFD7.wControlWord`
2. Observe se `rOutputFreq` mostra valores flutuando próximos de `0.0 Hz` (drive parado).
3. Se os valores ficarem em `0` estático (sem nenhuma flutuação), pode ser problema de comunicação — verifique IP e porta.

#### I.3 — Abrir a WebVisu

1. No navegador (Chrome, Edge), acesse: `http://localhost:8080/webvisu.htm`
   - (Porta pode variar conforme configuração do runtime — padrão CODESYS Control Win é 8080.)
2. Você deve ver o painel EM3P (do Lab 03) **e** o novo painel VFD7.

#### I.4 — Teste: Partida e Parada

1. No painel WebVisu, defina a frequência de referência via slider ou campo de entrada: **30 Hz**.
2. Clique em **START FWD**.
3. **No Watch Window e no smartphone:** observe:
   - `GVL_VFD7.bStartFwd` vai para `TRUE` por um ciclo e volta para `FALSE` (auto-reset).
   - `GVL_VFD7.wControlWord` muda para `1`.
   - `GVL_VFD7.rOutputFreq` começa a subir (rampa de aceleração).
   - No app do smartphone VFD7, o LED **RUN** acende em verde.
4. Aguarde até `rOutputFreq` estabilizar próximo de 30 Hz.
5. Observe o campo `Em Referência` (bAtRef) mudar para `TRUE`.
6. Na WebVisu, o **Trend** mostrará a curva de aceleração.

#### I.5 — Teste: Mudança de Frequência

> **ATENÇÃO — Prática segura de VFD:** Em sistemas reais, mudar a frequência de referência enquanto o drive está rodando é possível, mas pode causar trancos mecânicos ou picos de corrente. A boa prática industrial é:
> 1. Enviar STOP.
> 2. Aguardar o drive parar completamente (rOutputFreq < 0.5 Hz).
> 3. Definir a nova referência.
> 4. Enviar START novamente.
>
> Nesta prática, siga sempre esta sequência para desenvolver o hábito correto.

1. Clique em **STOP**. Aguarde `rOutputFreq` chegar a zero.
2. Ajuste o slider para **50 Hz**.
3. Clique em **START FWD**.
4. Observe a aceleração até 50 Hz na tendência.

#### I.6 — Teste: Reverse

1. Clique em **STOP**. Aguarde a parada completa.
2. Clique em **START REV**.
3. Observe:
   - `GVL_VFD7.wControlWord` = `3`.
   - `GVL_VFD7.bReverse` = `TRUE`, `bForward` = `FALSE`.
   - No smartphone: LED **REV** aceso.

#### I.7 — Teste: Leitura de Corrente e Potência

Com o drive rodando em 30 Hz:
1. Observe os campos `Corrente Saída` e `Potência Saída` na WebVisu.
2. Compare com os valores exibidos no LCD do smartphone VFD7.
3. Os valores devem ser compatíveis (tolerância de ±2% — diferença por taxa de atualização).

---

## 5. Critérios de Sucesso

Você completou esta prática se:

- Dois slaves aparecem sob o mesmo `Modbus_TCP_Master` no projeto CODESYS, cada um com IP diferente.
- Os 5 canais do VFD7 estão configurados e vinculados às variáveis da `GVL_VFD7`.
- O **Build** do projeto compila sem erros.
- Na WebVisu, o **Trend** mostra a rampa de frequência ao acionar START.
- Os botões START FWD, STOP e START REV funcionam — o drive responde e os valores de `rOutputFreq` e `wDriveStatus` mudam conforme esperado.
- Os campos de exibição (frequência, corrente, potência) mostram valores coerentes com o que o smartphone VFD7 exibe.
- O `bAtRef` muda para `TRUE` quando a frequência atinge o setpoint.
- O painel EM3P do Lab 03 **continua funcionando** simultaneamente.

---

## 6. Discussão e Reflexão

Responda no seu relatório:

1. **Múltiplos slaves, mesmo master.** Nesta prática, o `Modbus_TCP_Master` gerencia dois slaves (EM3P e VFD7) com IPs diferentes. Como o CODESYS diferencia as requisições para cada dispositivo? O que aconteceria se os dois tivessem o mesmo IP e porta?

2. **FC06 vs. FC16.** Por que usamos FC06 para escrever a Control Word (1 registrador UINT16) e FC16 para escrever a Frequency Reference (2 registradores FLOAT32)? Seria possível usar FC16 para tudo? Quais as implicações?

3. **Auto-reset dos BOOLs de comando.** O código faz `bStartFwd := FALSE` após enviar a Control Word. O que aconteceria se você **não** fizesse esse auto-reset? Considere o que aconteceria no ciclo seguinte do CLP.

4. **Segurança de operação.** No teste I.5, a instrução foi: pare antes de mudar a frequência. Em uma esteira de produção real, há situações onde mudar a frequência em movimento é **necessário e seguro**? Como você diferenciaria as situações em um programa real?

5. **Análise do Trend.** Com base na curva de frequência que você observou no Trend durante a aceleração, estime o **tempo de aceleração** (do start até At Reference). Esse valor corresponde ao parâmetro Acceleration Time (registrador 103–104) do VFD7? Verifique lendo esse registrador com FC03.

6. **Arquitetura SCADA.** Você construiu um supervisório mínimo com WebVisu. Um SCADA industrial real (ex.: Ignition, WinCC, FactoryTalk) adiciona que funcionalidades além do que você implementou? Liste pelo menos 4.

---

## 7. Entregáveis

Submeta um relatório PDF contendo:

1. **Captura da árvore de dispositivos** do CODESYS mostrando os dois slaves (EM3P e VFD7) sob o mesmo Master.

2. **Captura dos canais configurados** do `Modbus_TCP_Slave_VFD7` (os 5 canais com seus Function Codes, offsets e comprimentos).

3. **Código ST completo** das seções adicionadas ao PLC_PRG (decodificação, lógica de controle, codificação).

4. **Captura da WebVisu** mostrando:
   - O painel VFD7 **e** o painel EM3P simultaneamente.
   - O drive em operação (campos de frequência e corrente com valores não-zero).
   - O Trend com pelo menos uma curva de aceleração visível.

5. **Captura do smartphone VFD7** durante operação (LED RUN aceso, frequência no LCD).

6. **Tabela de teste** preenchida:

   | Ação                     | wControlWord esperado | rOutputFreq esperado | Resultado obtido |
   |--------------------------|----------------------|----------------------|------------------|
   | Após START FWD (30 Hz)   | 1                    | ~30.0 Hz             |                  |
   | Após atingir referência  | 1                    | 30.0 Hz, bAtRef=TRUE |                  |
   | Após STOP                | 0                    | ~0.0 Hz              |                  |
   | Após START REV (30 Hz)   | 3                    | ~30.0 Hz             |                  |

7. **Respostas** às 6 perguntas da seção 6.

---

## 8. Solução de Problemas

| Sintoma | Causa provável | Solução |
|---------|---------------|---------|
| Drive não responde aos botões | App VFD7 em modo LOCAL | Ative modo **REMOTE** no app |
| `rOutputFreq` sempre = 0.0 (estático) | Canal 1 não conecta ao VFD7 | Verifique IP e porta 5020 no Slave VFD7 |
| Control Word = 1 mas drive não parte | Canal 4 (FC06) não mapeado | Confirme vinculação de `wControlWord` no I/O Mapping |
| Frequência de referência não muda | Canal 5 não mapeado corretamente | Verifique `wFreqRef_Hi` e `wFreqRef_Lo` no I/O Mapping |
| FLOAT32 decodifica valor absurdo | High/Low word trocados | Confirme: `arWord[1]` = high, `arWord[0]` = low |
| Painel EM3P para de atualizar | Conflito de IP entre slaves | Confirme que cada slave tem IP diferente |
| Build com erro em `MODBUS_FLOAT32` | DUT não criado | Crie o DUT como descrito na seção G.1 |
| WebVisu não abre | Runtime não iniciado | Inicie o CODESYS Control Win runtime |
| bAtRef nunca fica TRUE | Frequência nunca atinge setpoint | Verifique se Max Frequency (reg 107-108) não está limitando |

---

## 9. Próximos Passos

- **[Prática Grupo 1 — 3 clientes / 1 VFD](11-pratica-grupo-1-3clientes-1vfd.md):** coordene três alunos com papéis distintos (operador, supervisor, manutenção) operando o mesmo inversor.
- **[Prática Grupo 4 — Mini-planta integrada](14-pratica-grupo-4-mini-planta.md):** integre o MK-EM3P e dois MK-VFD7 em uma mini-planta com lógica de intertravamento.

---

**Bom trabalho — e lembre-se: em automação industrial, o CLP que para de responder é mais grave do que o CLP que nunca funcionou.**
