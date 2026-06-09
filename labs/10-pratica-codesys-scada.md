# Prática 10 — SCADA Integrado CODESYS: MK-EM3P + MK-VFD7 com WebVisu

> *"Um SCADA real não é uma tela bonita — é a integração de dados, lógica e interface que permite a um operador tomar decisões corretas no momento certo."*

---

## 1. Contexto Industrial

Em instalações industriais modernas, raramente um CLP supervisiona apenas um dispositivo. Uma **subestação industrial típica** conecta simultaneamente:

- **Medidores de energia** (analisadores de qualidade) monitorando consumo, qualidade da tensão e alarmes elétricos.
- **Inversores de frequência** comandando motores de bomba, compressores, ventiladores, esteiras.
- **Sensores de campo** reportando temperatura, pressão, nível.

Toda essa informação converge para um **sistema SCADA** (*Supervisory Control And Data Acquisition*), que apresenta ao operador uma visão unificada da planta e permite ações de controle a partir de uma única interface.

O **CODESYS** é um ambiente de desenvolvimento de CLPs baseado em IEC 61131-3, com capacidade nativa de atuar como **Soft-PLC** — o computador convencional (um PC de engenharia ou um mini-computador industrial) executa a lógica de controle com polling determinístico via Modbus TCP. A função **WebVisu** expõe a interface gráfica como página web acessível de qualquer navegador na mesma rede, sem necessidade de software de HMI dedicado.

Nesta prática, você construirá um **SCADA completo** que:

1. Lê continuamente **todas as medições relevantes** do MK-EM3P (medidor de energia).
2. Controla e monitora o **MK-VFD7** (inversor de frequência).
3. Implementa um **interlock de potência**: se o consumo ultrapassar o limite configurado, o inversor é parado automaticamente.
4. Apresenta tudo em uma **única tela WebVisu** com botões, campos de entrada, slider, indicadores, tendências e alarme visual.

Esta é a **prática individual culminante** do ciclo CODESYS. Recomenda-se tê-la feito após as práticas individuais de EasyModbusTCP para o EM3P e para o VFD7, porém o guia é autocontido.

---

## 2. Conceitos Necessários

### 2.1 O que é um SCADA?

SCADA (*Supervisory Control And Data Acquisition*) é um sistema composto por quatro funções integradas:

| Função | O que faz |
|--------|-----------|
| **Aquisição de dados** | Lê continuamente variáveis de campo (Modbus, OPC UA, etc.) |
| **Supervisão** | Apresenta os dados ao operador em tempo real com tendências históricas |
| **Controle** | Permite ao operador enviar comandos e alterar setpoints |
| **Alarmes** | Detecta condições anormais e notifica o operador |

No contexto desta prática, o CODESYS Runtime cumpre o papel de **RTU** (*Remote Terminal Unit* / *PLC*), e o WebVisu é a **HMI** (*Human-Machine Interface*).

### 2.2 SoftPLC vs PLC dedicado

Um **SoftPLC** executa o programa IEC 61131-3 dentro de um processo de sistema operacional convencional. Vantagens para aprendizado: sem hardware dedicado, sem custo de licença por device. Limitação: não é determinístico no mesmo nível de um PLC de hardware. Para nossas práticas, a diferença é irrelevante.

### 2.3 Elementos do WebVisu usados nesta prática

| Elemento | Finalidade | Vinculação de variável |
|----------|-----------|------------------------|
| **Text Field** (Campo de texto) | Exibe valor numérico de uma variável | Propriedade `Text variable` |
| **Button** (Botão) | Executa uma ação ao clicar (escrever valor em variável) | Propriedade `Tap action → Write variable` |
| **Input Field** (Campo de entrada) | Permite ao operador digitar um valor numérico | Propriedade `Variable` |
| **Slider** | Controle deslizante para valores contínuos | Propriedade `Variable` |
| **Trend** (Tendência) | Gráfico histórico de uma ou mais variáveis ao longo do tempo | Cada canal aponta para uma variável |
| **Rectangle** (Retângulo) | Indicador visual de estado por cor | Propriedade `Color variable` |

> **Importante — WebVisu e tempo real:** O WebVisu atualiza via polling HTTP. O navegador solicita a tela a cada ciclo de atualização (padrão: 200 ms). Isso significa que **comandos não são instantâneos** — há um atraso inerente de até 200–500 ms entre o clique do operador e a execução da ação no PLC. Para aplicações de segurança crítica, isso é inaceitável. Para fins de controle supervisório e aprendizado, é adequado.

### 2.4 Interlock

Um **interlock** (intertravamento) é uma lógica de segurança que impede ou interrompe uma operação quando uma condição de risco é detectada. Nesta prática, o interlock implementado é:

> "Se a potência ativa total medida pelo MK-EM3P ultrapassar o limite de demanda configurado, o MK-VFD7 é parado automaticamente e um alarme visual é ativado."

Este é um interlock de **proteção de demanda elétrica** — comum em instalações onde o contrato de fornecimento de energia penaliza picos de consumo.

### 2.5 Relembrete: decodificação FLOAT32 (UNION T_Float32)

O Modbus transmite FLOAT32 como dois registradores de 16 bits em ordem ABCD (big-endian por palavra):

```iecst
TYPE T_Float32 :
UNION
    rValue  : REAL;
    arWord  : ARRAY[0..1] OF WORD;
END_UNION
END_TYPE
```

Atribuição após leitura Modbus:
```iecst
// arWord[1] recebe o primeiro registrador lido (palavra alta — bytes AB)
// arWord[0] recebe o segundo registrador lido (palavra baixa — bytes CD)
uFloat.arWord[1] := wRegHigh;
uFloat.arWord[0] := wRegLow;
rValorFinal := uFloat.rValue;
```

### 2.6 Mapa de registradores — referência consolidada

**MK-EM3P** (Smartphone 1, porta 5020, Unit ID 1):

| Endereço | Variável             | Tipo    | FC  | Unidade |
|----------|----------------------|---------|-----|---------|
| 0–1      | Voltage L1-N         | FLOAT32 | FC04| V       |
| 2–3      | Voltage L2-N         | FLOAT32 | FC04| V       |
| 4–5      | Voltage L3-N         | FLOAT32 | FC04| V       |
| 12–13    | Current L1           | FLOAT32 | FC04| A       |
| 14–15    | Current L2           | FLOAT32 | FC04| A       |
| 16–17    | Current L3           | FLOAT32 | FC04| A       |
| 26–27    | Active Power Total   | FLOAT32 | FC04| kW      |
| 50–51    | Power Factor Total   | FLOAT32 | FC04| —       |
| 52–53    | Frequency            | FLOAT32 | FC04| Hz      |
| 90       | Alarm Status         | UINT16  | FC04| bitmask |
| 91       | Device Status        | UINT16  | FC04| bitmask |
| 100      | CT Primary           | UINT16  | FC03| A       |
| 102      | VT Primary           | UINT16  | FC03| V       |

**MK-VFD7** (Smartphone 2, porta 5020, Unit ID 1):

| Endereço | Variável             | Tipo    | FC  | Unidade |
|----------|----------------------|---------|-----|---------|
| 0–1      | Output Frequency     | FLOAT32 | FC04| Hz      |
| 4–5      | Output Current       | FLOAT32 | FC04| A       |
| 6–7      | Output Power         | FLOAT32 | FC04| kW      |
| 26       | Drive Status         | UINT16  | FC04| bitmask |
| 100      | Control Word         | UINT16  | FC03| —       |
| 101–102  | Frequency Reference  | FLOAT32 | FC03| Hz      |
| 103–104  | Accel Time           | FLOAT32 | FC03| s       |
| 105–106  | Decel Time           | FLOAT32 | FC03| s       |
| 107–108  | Max Frequency        | FLOAT32 | FC03| Hz      |

---

## 3. Material e Setup

### 3.1 Hardware necessário

- **2 smartphones Android** com **ModbusDeviceSIM** instalado:
  - Smartphone 1: selecionar **MK-EM3P**
  - Smartphone 2: selecionar **MK-VFD7**, ativar modo **REMOTE**
- **1 laptop** com:
  - **CODESYS V3.5 SP19** ou superior (download gratuito em codesys.com)
  - **CODESYS Control Win V3** (SoftPLC, incluído no instalador padrão)
  - Navegador web moderno (Chrome, Firefox, Edge)
- **Rede Wi-Fi** comum aos 3 dispositivos (laptop + 2 smartphones)

### 3.2 Versões de software

| Software | Versão mínima | Observação |
|----------|--------------|-----------|
| CODESYS IDE | V3.5 SP19 | IDE de desenvolvimento |
| CODESYS Control Win V3 | qualquer | SoftPLC local, sem custo adicional |
| CODESYS WebVisu | incluído | Sem instalação separada |

### 3.3 Setup nos smartphones

**Smartphone 1 — MK-EM3P:**
1. Abra o ModbusDeviceSIM.
2. Selecione **MK-EM3P**.
3. Toque em **START**.
4. Anote o IP exibido. Exemplo: `192.168.1.101:5020`. Chamaremos de `IP_EM3P`.

**Smartphone 2 — MK-VFD7:**
1. Abra o ModbusDeviceSIM.
2. Selecione **MK-VFD7**.
3. Ative o switch **REMOTE** (necessário para aceitar comandos externos).
4. Toque em **START**.
5. Anote o IP exibido. Exemplo: `192.168.1.102:5020`. Chamaremos de `IP_VFD7`.

### 3.4 Verificação de conectividade

No laptop, abra o PowerShell e teste:

```
ping 192.168.1.101
ping 192.168.1.102
```

Ambos devem responder antes de prosseguir. Se algum não responder, verifique se os três dispositivos estão na mesma rede Wi-Fi.

---

## 4. Procedimento

### Parte A — Criação do Projeto CODESYS

> **Se você já tem um projeto das práticas anteriores (EasyModbusTCP + EM3P ou VFD7):** você pode criar um projeto novo limpo para esta prática. Manter projetos separados evita conflitos de configuração.

#### A.1 — Criar projeto novo

1. Abra o **CODESYS V3.5**.
2. Menu **File → New Project**.
3. Selecione **Standard project**.
4. Nome: `MK_SCADA_Integrado`.
5. Em "Device": selecione **CODESYS Control Win V3 x64** (SoftPLC local).
6. Em "PLC_PRG Language": selecione **Structured Text (ST)**.
7. Clique **OK**.

#### A.2 — Iniciar o CODESYS Runtime

1. Menu **Tools → Update Device** (se necessário).
2. Menu **Online → Login** — clique em "Yes" para compilar e fazer o download.
3. Se o runtime não estiver em execução: menu **Tools → CODESYS Control Win Manager → Start**.
4. Após login bem-sucedido, você verá `[Login OK]` na barra de status.

#### A.3 — Adicionar Ethernet Adapter ao projeto

Na árvore de dispositivos (Device tree, aba **Devices**):

1. Clique com botão direito em **Device (CODESYS Control Win V3)**.
2. **Add Device → Fieldbuses → Ethernet Adapter**.
3. Selecione **Ethernet** e clique **Add Device**.
4. Clique duplo no **Ethernet** adicionado.
5. Na aba **General**: selecione a interface de rede conectada ao Wi-Fi (geralmente "Wi-Fi" ou "Ethernet").

#### A.4 — Adicionar Modbus TCP Master

1. Clique com botão direito em **Ethernet**.
2. **Add Device → Modbus → Modbus TCP Master**.
3. Clique **Add Device**.

#### A.5 — Adicionar Slave para o MK-EM3P

1. Clique com botão direito em **Modbus_TCP_Master**.
2. **Add Device → Modbus → Modbus TCP Slave**.
3. Nome sugerido: `Modbus_TCP_Slave_EM3P`.
4. Clique **Add Device**.
5. Clique duplo no slave recém-criado.
6. Aba **General**:
   - **IP Address**: `192.168.1.101` (use o IP do Smartphone 1)
   - **Port**: `5020`
   - **Unit ID**: `1`

#### A.6 — Adicionar Slave para o MK-VFD7

1. Clique com botão direito em **Modbus_TCP_Master** (mesmo master).
2. **Add Device → Modbus → Modbus TCP Slave**.
3. Nome sugerido: `Modbus_TCP_Slave_VFD7`.
4. Clique **Add Device**.
5. Clique duplo no slave:
   - **IP Address**: `192.168.1.102` (use o IP do Smartphone 2)
   - **Port**: `5020`
   - **Unit ID**: `1`

> **Nota:** Os dois slaves compartilham o mesmo Master TCP. O CODESYS gerencia o polling sequencial entre eles.

---

### Parte B — Configuração dos Canais Modbus

Agora configuramos quais registradores cada slave deve ler ou escrever a cada ciclo.

#### B.1 — Canais do MK-EM3P

Clique duplo em **Modbus_TCP_Slave_EM3P** → aba **Modbus Slave Channel**.

Clique em **Add Channel** para cada linha abaixo:

| Nome do Canal        | Leitura/Escrita | Função Code | Offset | Comprimento | Comentário               |
|---------------------|-----------------|-------------|--------|-------------|--------------------------|
| `CH_EM3P_IR_0_91`   | Read            | FC04 (3x)   | 0      | 92          | Medições (endereços 0–91) |
| `CH_EM3P_HR_100_103`| Read            | FC03 (4x)   | 100    | 4           | Config CT/VT (100–103)   |
| `CH_EM3P_HR_WRITE`  | Write           | FC03 (4x)   | 100    | 4           | Escrever CT/VT           |

> **Por que dois canais para HR?** O CODESYS Modbus Slave separa canais de leitura (polling periódico) de escrita (acionados por alteração de variável). Você precisará de um canal Read para ler o valor atual e um canal Write separado para enviar novos valores.

#### B.2 — Canais do MK-VFD7

Clique duplo em **Modbus_TCP_Slave_VFD7** → aba **Modbus Slave Channel**.

| Nome do Canal        | Leitura/Escrita | Função Code | Offset | Comprimento | Comentário                |
|---------------------|-----------------|-------------|--------|-------------|---------------------------|
| `CH_VFD7_IR_0_27`   | Read            | FC04 (3x)   | 0      | 28          | Freq, Current, Power, Status |
| `CH_VFD7_HR_100_108`| Read            | FC03 (4x)   | 100    | 9           | Leitura Control Word + params |
| `CH_VFD7_HR_WRITE`  | Write           | FC03 (4x)   | 100    | 9           | Escrever Control Word + params |

---

### Parte C — Mapeamento I/O (I/O Mapping)

O mapeamento I/O conecta os canais Modbus aos arrays de variáveis do PLC.

#### C.1 — I/O Mapping do MK-EM3P

Clique duplo em **Modbus_TCP_Slave_EM3P** → aba **Modbus Slave I/O Mapping**.

Para o canal `CH_EM3P_IR_0_91`, mapeie o array de saída para a variável:
```
GVL_EM3P.arInputRegs
```

Para o canal `CH_EM3P_HR_100_103` (leitura), mapeie para:
```
GVL_EM3P.arHoldRegsRead
```

Para o canal `CH_EM3P_HR_WRITE` (escrita), mapeie para:
```
GVL_EM3P.arHoldRegsWrite
```

> **Como mapear:** No I/O Mapping, clique na coluna "Variable" da linha correspondente ao canal. Digite o nome da variável (declarada na Parte E). A variável deve existir antes do mapeamento; declare as GVLs primeiro se encontrar erros de compilação.

#### C.2 — I/O Mapping do MK-VFD7

Da mesma forma, clique duplo em **Modbus_TCP_Slave_VFD7** → aba **Modbus Slave I/O Mapping**:

| Canal                | Tipo    | Variável                  |
|---------------------|---------|---------------------------|
| `CH_VFD7_IR_0_27`   | Saída   | `GVL_VFD7.arInputRegs`    |
| `CH_VFD7_HR_100_108`| Saída   | `GVL_VFD7.arHoldRegsRead` |
| `CH_VFD7_HR_WRITE`  | Entrada | `GVL_VFD7.arHoldRegsWrite`|

---

### Parte D — DUT T_Float32 (UNION para decodificação FLOAT32)

Se você não tem este tipo de dado do projeto anterior, crie-o agora:

1. Na árvore de projeto (aba **POUs**), clique com botão direito em **Application**.
2. **Add Object → DUT (Data Unit Type)**.
3. Nome: `T_Float32`. Tipo: **Union**.
4. Cole o código:

```iecst
TYPE T_Float32 :
UNION
    rValue  : REAL;
    arWord  : ARRAY[0..1] OF WORD;
END_UNION
END_TYPE
```

5. Salve com **Ctrl+S**.

> **Por que UNION?** O UNION permite que as mesmas posições de memória sejam interpretadas como REAL ou como dois WORDs. Quando atribuímos `arWord[1]` e `arWord[0]`, estamos escrevendo bytes na memória; quando lemos `rValue`, o compilador interpreta esses mesmos bytes como IEEE 754 FLOAT32. Nenhuma cópia acontece — é uma reinterpretação direta.

---

### Parte E — Declaração das GVLs

Criaremos três GVLs (Global Variable Lists): uma por dispositivo e uma para o SCADA (interlock e parâmetros de operação).

#### E.1 — GVL_EM3P

1. Clique com botão direito em **Application → Add Object → Global Variable List**.
2. Nome: `GVL_EM3P`.
3. Insira o conteúdo:

```iecst
VAR_GLOBAL
    // --- Arrays brutos vindos do I/O Mapping ---
    arInputRegs     : ARRAY[0..91] OF WORD;     // FC04, end. 0–91
    arHoldRegsRead  : ARRAY[0..3]  OF WORD;     // FC03 leitura, end. 100–103
    arHoldRegsWrite : ARRAY[0..3]  OF WORD;     // FC03 escrita, end. 100–103

    // --- Medições decodificadas ---
    rVoltageL1      : REAL;   // V L1-N [V]
    rVoltageL2      : REAL;   // V L2-N [V]
    rVoltageL3      : REAL;   // V L3-N [V]
    rCurrentL1      : REAL;   // I L1 [A]
    rCurrentL2      : REAL;   // I L2 [A]
    rCurrentL3      : REAL;   // I L3 [A]
    rActivePower    : REAL;   // Potência Ativa Total [kW]
    rPowerFactor    : REAL;   // Fator de Potência Total
    rFrequency      : REAL;   // Frequência da rede [Hz]
    wAlarmStatus    : WORD;   // Status de alarmes (bitmask)
    wDeviceStatus   : WORD;   // Status do dispositivo (bitmask)

    // --- Configurações (lidas do dispositivo) ---
    wCTPrimary      : WORD;   // TC Primário [A]   (reg 100)
    wVTPrimary      : WORD;   // TP Primário [V]   (reg 102)

    // --- Setpoints para escrita ---
    wCTPrimarySet   : WORD;   // Novo valor TC a escrever
    wVTPrimarySet   : WORD;   // Novo valor TP a escrever
    bWriteConfig    : BOOL;   // Pulso para acionar escrita
END_VAR
```

#### E.2 — GVL_VFD7

1. Clique com botão direito em **Application → Add Object → Global Variable List**.
2. Nome: `GVL_VFD7`.
3. Insira o conteúdo:

```iecst
VAR_GLOBAL
    // --- Arrays brutos vindos do I/O Mapping ---
    arInputRegs     : ARRAY[0..27] OF WORD;     // FC04, end. 0–27
    arHoldRegsRead  : ARRAY[0..8]  OF WORD;     // FC03 leitura, end. 100–108
    arHoldRegsWrite : ARRAY[0..8]  OF WORD;     // FC03 escrita, end. 100–108

    // --- Medições decodificadas ---
    rOutputFreq     : REAL;   // Frequência de saída [Hz]
    rOutputCurrent  : REAL;   // Corrente de saída [A]
    rOutputPower    : REAL;   // Potência de saída [kW]
    wDriveStatus    : WORD;   // Status do drive (bitmask)

    // --- Controle ---
    wControlWord    : WORD;   // Palavra de controle (0=stop, 1=fwd, 3=rev)
    rFreqReference  : REAL;   // Referência de frequência [Hz]
    rAccelTime      : REAL;   // Tempo de aceleração [s]
    rDecelTime      : REAL;   // Tempo de desaceleração [s]
    rMaxFreq        : REAL;   // Frequência máxima [Hz]
    bWriteControl   : BOOL;   // Pulso para escrever Control Word
    bWriteParams    : BOOL;   // Pulso para escrever parâmetros
END_VAR
```

#### E.3 — GVL_SCADA

1. Clique com botão direito em **Application → Add Object → Global Variable List**.
2. Nome: `GVL_SCADA`.
3. Insira o conteúdo:

```iecst
VAR_GLOBAL
    // --- Interlock de potência ---
    rPowerThreshold : REAL := 15.0;   // Limite de demanda [kW] — ajustável pelo operador
    bPowerAlarm     : BOOL;           // TRUE quando potência excede limite
    bResetAlarm     : BOOL;           // Pulso de reset (botão na tela)

    // --- Comandos do operador (acionados pelos botões do WebVisu) ---
    bCmdStart       : BOOL;   // Botão START FRENTE
    bCmdStop        : BOOL;   // Botão STOP
    bCmdReverse     : BOOL;   // Botão START RÉ
END_VAR
```

---

### Parte F — PLC_PRG: Lógica Completa em Structured Text

Clique duplo em **PLC_PRG** na árvore de POUs. Substitua todo o conteúdo pelo código abaixo.

```iecst
PROGRAM PLC_PRG
VAR
    // --- Variáveis auxiliares para decodificação FLOAT32 ---
    uF : T_Float32;

    // --- Temporizadores para escrita (garante pulso único) ---
    bWriteEM3P_prev  : BOOL;
    bWriteVFD7C_prev : BOOL;
    bWriteVFD7P_prev : BOOL;
    bCmdStart_prev   : BOOL;
    bCmdStop_prev    : BOOL;
    bCmdRev_prev     : BOOL;
END_VAR

// ============================================================
//  BLOCO 1 — Decodificação MK-EM3P
//  Converte registradores brutos em variáveis REAL e WORD
// ============================================================

// Voltage L1-N  (registradores 0 e 1 do array)
uF.arWord[1] := GVL_EM3P.arInputRegs[0];
uF.arWord[0] := GVL_EM3P.arInputRegs[1];
GVL_EM3P.rVoltageL1 := uF.rValue;

// Voltage L2-N  (registradores 2 e 3)
uF.arWord[1] := GVL_EM3P.arInputRegs[2];
uF.arWord[0] := GVL_EM3P.arInputRegs[3];
GVL_EM3P.rVoltageL2 := uF.rValue;

// Voltage L3-N  (registradores 4 e 5)
uF.arWord[1] := GVL_EM3P.arInputRegs[4];
uF.arWord[0] := GVL_EM3P.arInputRegs[5];
GVL_EM3P.rVoltageL3 := uF.rValue;

// Current L1  (registradores 12 e 13)
uF.arWord[1] := GVL_EM3P.arInputRegs[12];
uF.arWord[0] := GVL_EM3P.arInputRegs[13];
GVL_EM3P.rCurrentL1 := uF.rValue;

// Current L2  (registradores 14 e 15)
uF.arWord[1] := GVL_EM3P.arInputRegs[14];
uF.arWord[0] := GVL_EM3P.arInputRegs[15];
GVL_EM3P.rCurrentL2 := uF.rValue;

// Current L3  (registradores 16 e 17)
uF.arWord[1] := GVL_EM3P.arInputRegs[16];
uF.arWord[0] := GVL_EM3P.arInputRegs[17];
GVL_EM3P.rCurrentL3 := uF.rValue;

// Active Power Total  (registradores 26 e 27)
uF.arWord[1] := GVL_EM3P.arInputRegs[26];
uF.arWord[0] := GVL_EM3P.arInputRegs[27];
GVL_EM3P.rActivePower := uF.rValue;

// Power Factor Total  (registradores 50 e 51)
uF.arWord[1] := GVL_EM3P.arInputRegs[50];
uF.arWord[0] := GVL_EM3P.arInputRegs[51];
GVL_EM3P.rPowerFactor := uF.rValue;

// Frequency  (registradores 52 e 53)
uF.arWord[1] := GVL_EM3P.arInputRegs[52];
uF.arWord[0] := GVL_EM3P.arInputRegs[53];
GVL_EM3P.rFrequency := uF.rValue;

// Alarm Status e Device Status  (UINT16 — cópia direta)
GVL_EM3P.wAlarmStatus  := GVL_EM3P.arInputRegs[90];
GVL_EM3P.wDeviceStatus := GVL_EM3P.arInputRegs[91];

// CT Primary e VT Primary (lidos via FC03)
GVL_EM3P.wCTPrimary := GVL_EM3P.arHoldRegsRead[0];   // reg 100
GVL_EM3P.wVTPrimary := GVL_EM3P.arHoldRegsRead[2];   // reg 102

// ============================================================
//  BLOCO 2 — Escrita de configuração do MK-EM3P
//  Detecta borda de subida em bWriteConfig e copia os setpoints
//  para o array de escrita I/O (mapeado ao canal CH_EM3P_HR_WRITE)
// ============================================================

IF GVL_EM3P.bWriteConfig AND NOT bWriteEM3P_prev THEN
    GVL_EM3P.arHoldRegsWrite[0] := GVL_EM3P.wCTPrimarySet;   // reg 100
    GVL_EM3P.arHoldRegsWrite[1] := 0;                          // reg 101 (reservado)
    GVL_EM3P.arHoldRegsWrite[2] := GVL_EM3P.wVTPrimarySet;   // reg 102
    GVL_EM3P.arHoldRegsWrite[3] := 0;                          // reg 103 (reservado)
    GVL_EM3P.bWriteConfig := FALSE;
END_IF
bWriteEM3P_prev := GVL_EM3P.bWriteConfig;

// ============================================================
//  BLOCO 3 — Decodificação MK-VFD7
// ============================================================

// Output Frequency  (registradores 0 e 1)
uF.arWord[1] := GVL_VFD7.arInputRegs[0];
uF.arWord[0] := GVL_VFD7.arInputRegs[1];
GVL_VFD7.rOutputFreq := uF.rValue;

// Output Current  (registradores 4 e 5)
uF.arWord[1] := GVL_VFD7.arInputRegs[4];
uF.arWord[0] := GVL_VFD7.arInputRegs[5];
GVL_VFD7.rOutputCurrent := uF.rValue;

// Output Power  (registradores 6 e 7)
uF.arWord[1] := GVL_VFD7.arInputRegs[6];
uF.arWord[0] := GVL_VFD7.arInputRegs[7];
GVL_VFD7.rOutputPower := uF.rValue;

// Drive Status  (UINT16, registrador 26)
GVL_VFD7.wDriveStatus := GVL_VFD7.arInputRegs[26];

// Leitura do Control Word atual (FC03, reg 100 = índice 0 do array hold)
GVL_VFD7.wControlWord := GVL_VFD7.arHoldRegsRead[0];

// Leitura da Frequency Reference atual (FC03, reg 101–102 = índices 1–2)
uF.arWord[1] := GVL_VFD7.arHoldRegsRead[1];
uF.arWord[0] := GVL_VFD7.arHoldRegsRead[2];
GVL_VFD7.rFreqReference := uF.rValue;

// Accel Time (FC03, reg 103–104 = índices 3–4)
uF.arWord[1] := GVL_VFD7.arHoldRegsRead[3];
uF.arWord[0] := GVL_VFD7.arHoldRegsRead[4];
GVL_VFD7.rAccelTime := uF.rValue;

// Decel Time (FC03, reg 105–106 = índices 5–6)
uF.arWord[1] := GVL_VFD7.arHoldRegsRead[5];
uF.arWord[0] := GVL_VFD7.arHoldRegsRead[6];
GVL_VFD7.rDecelTime := uF.rValue;

// Max Frequency (FC03, reg 107–108 = índices 7–8)
uF.arWord[1] := GVL_VFD7.arHoldRegsRead[7];
uF.arWord[0] := GVL_VFD7.arHoldRegsRead[8];
GVL_VFD7.rMaxFreq := uF.rValue;

// ============================================================
//  BLOCO 4 — Lógica de controle do VFD7
//  Botões do WebVisu → Control Word no array de escrita
// ============================================================

// START FRENTE — borda de subida em bCmdStart
IF GVL_SCADA.bCmdStart AND NOT bCmdStart_prev THEN
    GVL_VFD7.arHoldRegsWrite[0] := 1;   // Control Word = 1 (Run Forward)
    GVL_VFD7.bWriteControl := TRUE;
    GVL_SCADA.bCmdStart := FALSE;
END_IF
bCmdStart_prev := GVL_SCADA.bCmdStart;

// STOP — borda de subida em bCmdStop
IF GVL_SCADA.bCmdStop AND NOT bCmdStop_prev THEN
    GVL_VFD7.arHoldRegsWrite[0] := 0;   // Control Word = 0 (Stop)
    GVL_VFD7.bWriteControl := TRUE;
    GVL_SCADA.bCmdStop := FALSE;
END_IF
bCmdStop_prev := GVL_SCADA.bCmdStop;

// START RÉ — borda de subida em bCmdReverse
IF GVL_SCADA.bCmdReverse AND NOT bCmdRev_prev THEN
    GVL_VFD7.arHoldRegsWrite[0] := 3;   // Control Word = 3 (Run Reverse)
    GVL_VFD7.bWriteControl := TRUE;
    GVL_SCADA.bCmdReverse := FALSE;
END_IF
bCmdRev_prev := GVL_SCADA.bCmdReverse;

// Escrita de parâmetros (Freq Reference, Accel, Decel)
IF GVL_VFD7.bWriteParams AND NOT bWriteVFD7P_prev THEN
    // Control Word (reg 100, índice 0) — mantém valor atual
    GVL_VFD7.arHoldRegsWrite[0] := GVL_VFD7.wControlWord;

    // Frequency Reference (reg 101–102, índices 1–2)
    uF.rValue := GVL_VFD7.rFreqReference;
    GVL_VFD7.arHoldRegsWrite[1] := uF.arWord[1];
    GVL_VFD7.arHoldRegsWrite[2] := uF.arWord[0];

    // Accel Time (reg 103–104, índices 3–4)
    uF.rValue := GVL_VFD7.rAccelTime;
    GVL_VFD7.arHoldRegsWrite[3] := uF.arWord[1];
    GVL_VFD7.arHoldRegsWrite[4] := uF.arWord[0];

    // Decel Time (reg 105–106, índices 5–6)
    uF.rValue := GVL_VFD7.rDecelTime;
    GVL_VFD7.arHoldRegsWrite[5] := uF.arWord[1];
    GVL_VFD7.arHoldRegsWrite[6] := uF.arWord[0];

    // Max Freq (reg 107–108, índices 7–8) — mantém valor atual
    uF.rValue := GVL_VFD7.rMaxFreq;
    GVL_VFD7.arHoldRegsWrite[7] := uF.arWord[1];
    GVL_VFD7.arHoldRegsWrite[8] := uF.arWord[0];

    GVL_VFD7.bWriteParams := FALSE;
END_IF
bWriteVFD7P_prev := GVL_VFD7.bWriteParams;

// Escrita do Control Word (acionado internamente pelos comandos START/STOP/REV)
IF GVL_VFD7.bWriteControl AND NOT bWriteVFD7C_prev THEN
    GVL_VFD7.bWriteControl := FALSE;
END_IF
bWriteVFD7C_prev := GVL_VFD7.bWriteControl;

// ============================================================
//  BLOCO 5 — Interlock de potência (SCADA)
//  Se potência ativa > limite → para o VFD e aciona alarme
// ============================================================

IF GVL_EM3P.rActivePower > GVL_SCADA.rPowerThreshold THEN
    GVL_VFD7.arHoldRegsWrite[0] := 0;     // Control Word = 0 (STOP)
    GVL_VFD7.bWriteControl := TRUE;
    GVL_SCADA.bPowerAlarm := TRUE;
END_IF

// Reset do alarme (botão RESET ALARM no WebVisu)
IF GVL_SCADA.bResetAlarm THEN
    GVL_SCADA.bPowerAlarm := FALSE;
    GVL_SCADA.bResetAlarm := FALSE;
END_IF
```

Salve com **Ctrl+S**. Compile com **Build → Build** e verifique que não há erros.

> **Atenção:** Se você receber erro `Identifier 'T_Float32' is undefined`, certifique-se de ter criado o DUT na Parte D antes de compilar o PLC_PRG.

---

### Parte G — Construção do WebVisu SCADA

Esta é a seção central desta prática. Vamos construir a interface passo a passo, elemento por elemento.

#### G.1 — Criar a Visualização

1. Na árvore do projeto, clique com botão direito em **Application**.
2. **Add Object → Visualization**.
3. Nome: `SCADA`.
4. Clique **Open** para abrir o editor visual.

A tela do WebVisu é uma área de pixels (padrão 1024 × 768). Você posiciona e dimensiona elementos arrastando ou editando as coordenadas nas propriedades.

> **Dica de layout:** use o menu **Visualization → Canvas Properties** para ajustar o tamanho da tela. Para esta prática, 1280 × 800 pixels é recomendado.

#### G.2 — Título e Indicador de Alarme

**Adicionar texto de título:**

1. Na barra de ferramentas da Visualization, clique no ícone **Rectangle** (retângulo).
2. Desenhe um retângulo estreito no topo da tela (ex.: 20, 10 a 1260, 60).
3. Nas propriedades (**Properties** à direita):
   - **Texts → Text**: `MK-SCADA — Mekatronik Advanced Engineering`
   - **Font**: tamanho 18, negrito
   - **Colors → Fill color**: `#0070F0` (azul Mekatronik)
   - **Colors → Text color**: branco

**Adicionar indicador de alarme (retângulo com cor variável):**

O indicador de alarme usa a propriedade **Color Variable** para mudar a cor do retângulo conforme o valor de uma variável BOOL.

1. Adicione um novo **Rectangle** no canto superior esquerdo (ex.: 20, 70 a 200, 110).
2. Nas propriedades:
   - **Texts → Text**: `ALARME DE POTÊNCIA`
   - **Font**: tamanho 12, negrito
3. Na seção **Colors**:
   - **Fill color**: `#00AA00` (verde — cor padrão quando alarme FALSE)
4. Clique em **Color Variables** (ou "Farbe Variable" em instalações em alemão):
   - **Color Variable**: `GVL_SCADA.bPowerAlarm`
   - **Color when TRUE**: `#FF0000` (vermelho)
   - **Color when FALSE**: `#00AA00` (verde)

> **Como funciona:** O CODESYS WebVisu monitora a variável `GVL_SCADA.bPowerAlarm`. Quando `TRUE`, pinta o retângulo de vermelho; quando `FALSE`, de verde. Este é o método padrão para indicadores de estado binário no WebVisu.

#### G.3 — Painel MK-EM3P (lado esquerdo)

**Cabeçalho do painel EM3P:**

1. Adicione um **Rectangle** (ex.: 20, 120 a 620, 160).
2. **Texts → Text**: `MK-EM3P — Medidor de Energia`
3. Fill color: `#004499` (azul escuro). Text color: branco.

**Text Fields (campos de exibição) para o EM3P:**

Para cada variável abaixo, adicione um elemento **Text Field** (ou **Label + Text Field** lado a lado):

Como adicionar um Text Field:
1. Clique no ícone **Text Field** na barra de ferramentas.
2. Desenhe o campo na posição desejada.
3. Nas propriedades:
   - **Texts → Text variable**: nome da variável GVL (ex.: `GVL_EM3P.rVoltageL1`)
   - **Texts → Text**: deixe vazio (o valor da variável substituirá)
   - **Number format**: `%.2f` para 2 casas decimais

Adicione os seguintes campos (label estático ao lado para identificação):

| Label estático (Rectangle ou Text) | Text Field — variável vinculada     | Unidade |
|------------------------------------|-------------------------------------|---------|
| `V L1-N:`                          | `GVL_EM3P.rVoltageL1`               | `V`     |
| `V L2-N:`                          | `GVL_EM3P.rVoltageL2`               | `V`     |
| `V L3-N:`                          | `GVL_EM3P.rVoltageL3`               | `V`     |
| `I L1:`                            | `GVL_EM3P.rCurrentL1`               | `A`     |
| `P Ativa Total:`                   | `GVL_EM3P.rActivePower`             | `kW`    |
| `Fator de Potência:`               | `GVL_EM3P.rPowerFactor`             | `—`     |
| `Frequência:`                      | `GVL_EM3P.rFrequency`               | `Hz`    |

> **Dica:** para o campo de Potência Ativa, considere mudar a cor do texto para vermelho quando `GVL_SCADA.bPowerAlarm` estiver TRUE. Use a propriedade **Font Variables → Color variable** do Text Field e configure da mesma forma que o retângulo de alarme.

#### G.4 — Tendência 1: Tensão L1 e Potência Ativa (EM3P)

A **Trend** (elemento de tendência) é um dos elementos mais poderosos do WebVisu — permite visualizar o histórico de variáveis ao longo do tempo.

Como adicionar uma Trend:

1. Na barra de ferramentas da Visualization, clique em **Trend** (ícone de gráfico).
2. Desenhe a área do gráfico (ex.: 20, 480 a 620, 660).
3. Nas propriedades, clique em **Trend** na lista de categorias:
   - **Time range (seconds)**: `60` (mostra os últimos 60 segundos)
   - **Update time (ms)**: `500`

**Adicionar Canal 1 — Tensão L1:**
4. Na seção **Trend Channels**, clique em **Add**.
5. Configure:
   - **Variable**: `GVL_EM3P.rVoltageL1`
   - **Channel name**: `V L1-N`
   - **Color**: azul (`#0070F0`)
   - **Y-Axis Min**: `180`, **Y-Axis Max**: `260`

**Adicionar Canal 2 — Potência Ativa:**
6. Clique novamente em **Add** para um segundo canal.
7. Configure:
   - **Variable**: `GVL_EM3P.rActivePower`
   - **Channel name**: `P Ativa [kW]`
   - **Color**: vermelho (`#FF4400`)
   - **Y-Axis Min**: `0`, **Y-Axis Max**: `30`
   - **Y-Axis**: selecione "Y-Axis 2" (eixo secundário à direita)

> **Nota sobre eixos secundários:** Como Tensão (V) e Potência (kW) têm escalas muito diferentes, use dois eixos Y (Y-Axis 1 e Y-Axis 2). O CODESYS Trend suporta até 4 eixos Y independentes.

#### G.5 — Painel MK-VFD7 (lado direito)

**Cabeçalho do painel VFD7:**

1. Adicione um **Rectangle** (ex.: 640, 120 a 1260, 160).
2. **Texts → Text**: `MK-VFD7 — Inversor de Frequência`
3. Fill color: `#AA3300` (vermelho-escuro Mekatronik). Text color: branco.

**Text Fields para o VFD7:**

| Label estático          | Text Field — variável vinculada  | Unidade |
|------------------------|----------------------------------|---------|
| `Freq. Saída:`         | `GVL_VFD7.rOutputFreq`           | `Hz`    |
| `Corrente Saída:`      | `GVL_VFD7.rOutputCurrent`        | `A`     |
| `Potência Saída:`      | `GVL_VFD7.rOutputPower`          | `kW`    |
| `Status Drive:`        | `GVL_VFD7.wDriveStatus`          | `—`     |

#### G.6 — Botões de Controle do VFD7

**Como adicionar um botão no WebVisu:**

1. Na barra de ferramentas, clique em **Button** (ou Rectangle — botões são retângulos com ação).
2. Desenhe o botão na posição desejada.
3. Nas propriedades, seção **Texts**:
   - **Text**: `START FRENTE` (texto exibido no botão)
4. Seção **Events → Tap** (ou "On Mouse Click"):
   - Clique em **Add** → selecione **Write variable**.
   - **Variable**: `GVL_SCADA.bCmdStart`
   - **Value**: `TRUE`
5. Para resetar o botão visualmente, você pode usar o fundo verde neste botão.

Adicione os quatro botões:

| Texto no Botão  | Variável             | Valor escrito | Fill Color    |
|----------------|----------------------|---------------|---------------|
| `START FRENTE` | `GVL_SCADA.bCmdStart`  | `TRUE`      | `#007700` (verde) |
| `STOP`         | `GVL_SCADA.bCmdStop`   | `TRUE`      | `#CC0000` (vermelho) |
| `START RÉ`     | `GVL_SCADA.bCmdReverse`| `TRUE`      | `#FF8800` (laranja) |
| `RESET ALARME` | `GVL_SCADA.bResetAlarm`| `TRUE`      | `#555555` (cinza) |

> **Como o botão funciona na lógica:** O PLC_PRG detecta a borda de subida de `bCmdStart` (TRUE para FALSE). Após executar a ação, o código zera a variável (`bCmdStart := FALSE`). No próximo ciclo, o botão volta ao visual "solto". Esse padrão evita comandos repetidos enquanto o botão fica pressionado.

#### G.7 — Slider: Referência de Frequência

O slider permite ajuste contínuo da frequência de referência do VFD.

1. Na barra de ferramentas, clique em **Slider** (controle deslizante).
2. Desenhe na posição desejada (ex.: 640, 420 a 1060, 450).
3. Nas propriedades:
   - **Variable**: `GVL_VFD7.rFreqReference`
   - **Minimum**: `0`
   - **Maximum**: `60`
   - **Orientation**: Horizontal

> **Nota:** o slider modifica diretamente `GVL_VFD7.rFreqReference`. O valor só é enviado ao VFD quando o operador clicar no botão "Aplicar Params" (que aciona `bWriteParams`). Isso evita envios contínuos para o Modbus a cada movimento do slider.

#### G.8 — Input Fields (Campos de Entrada)

Os Input Fields permitem que o operador digite valores numéricos diretamente.

**Como adicionar um Input Field:**

1. Na barra de ferramentas, clique em **Input Field** (ou **Text Input**).
2. Desenhe o campo na posição desejada.
3. Nas propriedades:
   - **Variable**: variável vinculada (ex.: `GVL_VFD7.rFreqReference`)
   - **Input type**: `Float` ou `Integer` conforme o tipo da variável
   - **Min/Max value**: limites de entrada segura

Adicione os seis campos de entrada:

| Label                 | Variável                     | Tipo    | Min  | Max   |
|----------------------|------------------------------|---------|------|-------|
| `Referência Freq.`   | `GVL_VFD7.rFreqReference`    | Float   | 0.0  | 60.0  |
| `Tempo Aceleração`   | `GVL_VFD7.rAccelTime`        | Float   | 0.5  | 60.0  |
| `Tempo Desaceleração`| `GVL_VFD7.rDecelTime`        | Float   | 0.5  | 60.0  |
| `TC Primário (A)`    | `GVL_EM3P.wCTPrimarySet`     | Integer | 1    | 9999  |
| `TP Primário (V)`    | `GVL_EM3P.wVTPrimarySet`     | Integer | 100  | 35000 |
| `Limite de Potência` | `GVL_SCADA.rPowerThreshold`  | Float   | 1.0  | 100.0 |

> **Por que Input Field e Slider para o mesmo dado?** São formas complementares de entrada. O slider é intuitivo para ajuste grosso; o input field permite precisão. Ambos escrevem na mesma variável `rFreqReference`. O operador usa o que preferir.

**Botão para aplicar parâmetros do VFD7:**

Adicione um botão extra `Aplicar Parâmetros` vinculado a:
- **Variable**: `GVL_VFD7.bWriteParams`
- **Value**: `TRUE`

**Botão para aplicar configurações do EM3P:**

Adicione um botão `Aplicar Config EM3P` vinculado a:
- **Variable**: `GVL_EM3P.bWriteConfig`
- **Value**: `TRUE`

#### G.9 — Tendência 2: Frequência de Saída do VFD7

1. Na barra de ferramentas, clique em **Trend**.
2. Desenhe a área do gráfico (ex.: 640, 480 a 1260, 660).
3. Propriedades:
   - **Time range**: `60` segundos
   - **Update time**: `500` ms

**Canal único — Output Frequency:**
4. **Add Channel**:
   - **Variable**: `GVL_VFD7.rOutputFreq`
   - **Channel name**: `Freq. Saída [Hz]`
   - **Color**: `#FF8800` (laranja)
   - **Y-Axis Min**: `0`, **Y-Axis Max**: `65`

#### G.10 — Painel de Configuração (parte inferior esquerda)

Agrupe os campos de configuração do EM3P e o botão RESET ALARME em um painel visual:

1. Adicione um **Rectangle** de fundo (ex.: 20, 670 a 620, 780).
2. Fill color: `#222222` (cinza escuro). Sem border.
3. **Texts → Text**: `Configuração e Alarmes`.
4. Dentro desse painel, posicione os Text Fields e Input Fields para:
   - CT Primary (exibição): `GVL_EM3P.wCTPrimary`
   - VT Primary (exibição): `GVL_EM3P.wVTPrimary`
   - CT Primary Set (input): `GVL_EM3P.wCTPrimarySet`
   - VT Primary Set (input): `GVL_EM3P.wVTPrimarySet`
   - Botão `Aplicar Config EM3P`
   - Botão `RESET ALARME`
   - Limite de Potência (input): `GVL_SCADA.rPowerThreshold`

#### G.11 — Ativar o WebVisu

Por padrão, o WebVisu precisa estar configurado para ser servido pelo CODESYS Runtime.

1. Clique duplo em **Visualization Manager** na árvore do projeto.
2. Certifique-se de que **WebVisu** está habilitado.
3. Anote a porta HTTP (padrão: `8080`).
4. Compile e faça Download (**Build → Build** e **Online → Login → Download**).
5. Coloque o PLC em **RUN** (**Debug → Start**).
6. Abra o navegador e acesse: `http://localhost:8080/webvisu.htm`

> **Acessar de outro dispositivo:** substitua `localhost` pelo IP do laptop (ex.: `http://192.168.1.100:8080/webvisu.htm`). O WebVisu é acessível de qualquer dispositivo na mesma rede — smartphone, tablet, outro computador.

> **Referência completa do WebVisu:** https://content.helpme-codesys.com/en/CODESYS%20Visualization/

---

### Parte H — Download e Teste

#### H.1 — Checklist de verificação

Antes de considerar a prática completa, verifique **cada item** abaixo:

**Conectividade:**
- [ ] Ping para Smartphone 1 (EM3P) responde
- [ ] Ping para Smartphone 2 (VFD7) responde
- [ ] Status do Master Modbus em CODESYS mostra ambos os slaves como `Connected`

**Dados do MK-EM3P:**
- [ ] Tensão L1-N exibe valor plausível (200–240 V)
- [ ] Tensão L2-N e L3-N exibem valores próximos ao L1
- [ ] Corrente L1 exibe valor maior que zero
- [ ] Potência Ativa exibe valor maior que zero
- [ ] Fator de Potência entre 0,0 e 1,0
- [ ] Frequência em torno de 60,0 Hz
- [ ] Trend 1 está se atualizando (linha se movendo)

**Dados do MK-VFD7:**
- [ ] Frequência de saída exibe valor (ou zero se parado)
- [ ] Status Drive exibe valor
- [ ] Trend 2 está se atualizando

**Controle do MK-VFD7:**
- [ ] Botão START FRENTE: VFD começa a girar (frequência sobe para valor de referência)
- [ ] Slider ou Input Field: alterar referência e clicar `Aplicar Parâmetros` muda a frequência
- [ ] Botão STOP: VFD para
- [ ] Botão START RÉ: VFD gira em sentido inverso (se suportado pelo modo do simulador)

**Interlock de potência:**
- [ ] Com VFD rodando, reduza o `Limite de Potência` para um valor abaixo da potência atual
- [ ] O VFD deve parar automaticamente
- [ ] O retângulo indicador de alarme deve ficar vermelho
- [ ] Botão RESET ALARME deve apagar o alarme (retângulo volta a verde)
- [ ] Aumentar o limite e pressionar START retoma a operação normalmente

**Configuração do EM3P:**
- [ ] Alterar CT Primary Set e clicar `Aplicar Config EM3P`: o campo de leitura CT Primary atualiza

#### H.2 — Diagnóstico de problemas comuns

| Sintoma | Causa provável | Solução |
|---------|---------------|---------|
| Slave aparece como `Disconnected` | IP errado ou app não rodando | Confirme IP no app; verifique REMOTE no VFD7 |
| Valores exibem 0,0 e não mudam | Canal Modbus não mapeado | Revise I/O Mapping (Parte C) |
| FLOAT32 exibe valor estranho (ex.: 4,6e18) | Ordem de palavras invertida | Confirme `arWord[1]` = high, `arWord[0]` = low |
| Botão não aciona VFD | Canal de escrita não configurado | Verifique canal `CH_VFD7_HR_WRITE` e I/O Mapping de escrita |
| WebVisu não abre | Runtime não em RUN | Verifique status no CODESYS Control Win Manager |
| Trend não exibe histórico | `Update time` não configurado | Abra propriedades da Trend e configure Update time |
| Interlock não para o VFD | Variável não está sendo gravada no write array | Verifique Bloco 5 do PLC_PRG e o canal de escrita |

---

## 5. Critérios de Sucesso

Você completou esta prática com sucesso se:

- [ ] **C1 — Conectividade dupla:** os dois slaves Modbus aparecem como `Connected` no CODESYS simultaneamente, com dados atualizando a cada ciclo.
- [ ] **C2 — Exibição completa EM3P:** os 7 campos de medição do EM3P (3 tensões, corrente, potência, FP, frequência) exibem valores plausíveis e oscilam levemente (efeito da simulação).
- [ ] **C3 — Controle funcional VFD7:** os botões START FRENTE, STOP e START RÉ alteram o estado do VFD; o slider e o campo de entrada modificam a frequência de referência; os parâmetros de aceleração/desaceleração são aceitos.
- [ ] **C4 — Interlock operacional:** ao configurar o limite de demanda abaixo da potência ativa atual, o VFD é parado automaticamente e o indicador de alarme fica vermelho; o RESET ALARME apaga o alarme.
- [ ] **C5 — WebVisu com todos os tipos de elemento:** a tela contém pelo menos: 2 Trends funcionando, 1 Slider, 4 Buttons, 6 Input Fields, multiplos Text Fields, 1 Rectangle indicador de alarme — todos com variáveis vinculadas corretamente.
- [ ] **C6 — Configuração EM3P gravável:** CT Primary e VT Primary podem ser alterados via input field e aplicados ao simulador, com confirmação pela leitura do valor atualizado.

---

## 6. Discussão e Reflexão

1. **Latência do WebVisu.** Esta prática usa WebVisu com polling HTTP a cada ~200–500 ms. Pesquise o que é o protocolo **OPC UA** e explique por que ele seria preferível ao WebVisu para uma aplicação de controle de segurança em que a latência máxima aceitável é de 50 ms.

2. **Interlock no PLC vs na HMI.** O interlock de potência foi implementado no **PLC_PRG** (no CLP), e não no WebVisu (na HMI). Qual é a diferença prática de segurança entre as duas abordagens? Em que situação o interlock na HMI falharia e o do CLP não falharia?

3. **Escrita com borda de subida.** O PLC_PRG usa detecção de borda (`AND NOT _prev`) para acionar a escrita de parâmetros. Por que usar borda em vez de escrever a variável diretamente no canal de escrita a cada ciclo? Quais problemas isso evitaria em um VFD real?

4. **Escalabilidade.** Nesta prática, você gerenciou 2 dispositivos com ~15 variáveis cada. Suponha que a planta cresça para 20 inversores e 5 medidores. Descreva dois desafios de engenharia que surgiriam ao escalar esse projeto CODESYS, e como você os abordaria (organização de GVLs, estrutura de dados, performance de polling).

5. **Qualidade de energia e interlock.** Atualmente, o interlock usa apenas a potência ativa total. Que outros parâmetros do MK-EM3P (`wAlarmStatus`, fator de potência, desequilíbrio de tensão) poderiam ser úteis em uma lógica de interlock mais robusta? Escreva em pseudocódigo IEC 61131-3 uma versão ampliada do interlock que considera pelo menos dois desses parâmetros adicionais.

---

## 7. Entregáveis

Submeta o seguinte para avaliação:

1. **Arquivo do projeto CODESYS** (`.project` ou `.zip` exportado pelo CODESYS) com todas as configurações, GVLs, PLC_PRG e a visualização SCADA.

2. **Capturas de tela do WebVisu** em operação:
   - Tela completa com VFD rodando em frente (dados do EM3P e VFD visíveis).
   - Tela mostrando o alarme de potência ativo (indicador vermelho).
   - Tela após o reset do alarme (indicador verde).
   - Tela das Trends com pelo menos 60 segundos de histórico visível.

3. **Relatório técnico** (1–2 páginas) descrevendo:
   - Os passos que apresentaram maior dificuldade e como foram resolvidos.
   - Os valores de CT Primary, VT Primary e Limite de Potência usados nos testes.
   - O valor de frequência de referência aplicado e o tempo de aceleração observado.

4. **Respostas às 5 perguntas** da seção 6.

5. **Código PLC_PRG completo** (pode ser o mesmo do projeto, mas destaque com comentários as seções onde você precisou adaptar endereços ou nomes de variáveis em relação ao guia).

---

## Referências e Próximos Passos

- **CODESYS Visualization Help:** https://content.helpme-codesys.com/en/CODESYS%20Visualization/
- **IEC 61131-3 Structured Text** — padrão da linguagem usada no PLC_PRG.
- **Próxima prática:** [Prática Grupo 4 — Mini-planta Integrada](14-pratica-grupo-4-mini-planta.md): equipe de 3 alunos, 2 VFDs e 1 medidor, com papéis distintos e política operacional coordenada.

---

**Bom trabalho — você construiu um SCADA industrial completo do zero.**
