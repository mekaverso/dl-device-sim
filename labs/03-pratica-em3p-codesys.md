# Prática 3 — MK-EM3P com CODESYS + WebVisu

> *"Quando o software PLC lê o medidor de energia e você vê os valores no browser — isso é SCADA."*

---

## 1. Contexto Industrial

Em plantas industriais modernas, **CLPs (Controladores Lógicos Programáveis)** são responsáveis não apenas pelo controle de máquinas, mas também pela **aquisição de dados de campo** — medidores de energia, inversores, sensores inteligentes. Ferramentas como o **CODESYS** implementam o padrão **IEC 61131-3**, a linguagem universal de programação de CLPs adotada por fabricantes como Schneider Electric, Wago, Pilz, Beckhoff e dezenas de outros.

O **SoftPLC** (CLP em software, rodando no PC) é muito usado em:

- **Protótipos e bancadas de desenvolvimento:** o engenheiro programa e testa sem precisar de hardware dedicado.
- **Sistemas embarcados Linux/Raspberry Pi:** o SoftPLC transforma um mini-PC em um CLP de baixo custo.
- **Formação profissional:** o aluno aprende a linguagem IEC 61131-3 real, com o mesmo ambiente que encontrará na indústria.

Nesta prática, você irá:

- Configurar o **CODESYS Development System** como cliente Modbus TCP para ler o MK-EM3P.
- Escrever código em **Structured Text (ST)** para decodificar os valores FLOAT32.
- Construir uma interface **WebVisu** acessível pelo browser — sua primeira tela SCADA funcional.

---

## 2. Conceitos Necessários

### 2.1 SoftPLC — O CLP em Software

Um **SoftPLC** é um processo de software que executa o ciclo de varredura de um CLP real:

```
  ┌─────────────────────────────────────────────────────────┐
  │  Ciclo de varredura do CLP (scan cycle)                 │
  │                                                         │
  │  1. Leitura das entradas (I/O)     ← módulos de campo   │
  │  2. Execução do programa (PLC_PRG) ← lógica do usuário  │
  │  3. Escrita nas saídas (I/O)       → módulos de campo   │
  │                                                         │
  │  Repetido a cada 10–50 ms (configurável)                │
  └─────────────────────────────────────────────────────────┘
```

O **CODESYS Control Win SysTray** é um SoftPLC gratuito para Windows que aparece como ícone na área de notificação do sistema. Ele executa aplicações CODESYS exatamente como um CLP físico faria.

### 2.2 Device Tree — A Árvore de Dispositivos

No CODESYS, a comunicação de campo é configurada visualmente em uma **árvore de dispositivos**:

```
  MyDevice (CODESYS Control Win SysTray)
  └── Application
      └── Ethernet Adapter
          └── Modbus_TCP_Master
              └── Modbus_TCP_Slave_1  ← um nó por dispositivo de campo
                  ├── Channel 1: FC04, regs 0–53   (tensões, correntes, potência)
                  ├── Channel 2: FC04, regs 90–91  (alarmes)
                  ├── Channel 3: FC03, regs 100–103 (configuração)
                  └── Channel 4: FC06, reg 100     (escrita do TC)
```

Cada **Channel** define:
- O **Function Code** (FC03, FC04, FC06, etc.)
- O **Register Offset** — endereço inicial no escravo
- O **Length** — quantidade de registradores a ler/escrever
- Se é leitura, o canal gera variáveis de **entrada** (`%IW`); se escrita, gera variáveis de **saída** (`%QW`).

### 2.3 I/O Mapping — Ligando Hardware a Variáveis

O **I/O Mapping** é a tabela que conecta os endereços físicos (`%IW0`, `%IW1`, ...) às variáveis do programa. Em vez de usar endereços numéricos no código (difícil de ler), você mapeia:

```
  %IW0  →  gvlEM3P.awVoltageBlock[0]   (high word de Voltage L1-N)
  %IW1  →  gvlEM3P.awVoltageBlock[1]   (low word  de Voltage L1-N)
  ...
```

Assim o código ST trabalha com nomes significativos, e o CLP cuida da comunicação física.

### 2.4 UNION em IEC 61131-3 — Decodificando FLOAT32

O padrão **IEC 61131-3** suporta o tipo `UNION` — uma estrutura onde todos os membros compartilham a mesma área de memória. Isso é exatamente o que precisamos para interpretar dois `WORD`s como um `REAL` (IEEE 754 FLOAT32):

```iecst
TYPE T_Float32 :
UNION
    arWord : ARRAY[0..1] OF WORD;   (* dois WORD = 32 bits *)
    rValue : REAL;                   (* o mesmo espaço lido como REAL *)
END_UNION
END_TYPE
```

Para decodificar um float ABCD (big-endian, padrão do MK-EM3P):

```iecst
uFloat.arWord[1] := wHighWord;   (* Word mais significativa = índice [1] *)
uFloat.arWord[0] := wLowWord;    (* Word menos significativa = índice [0] *)
rResultado := uFloat.rValue;     (* lê os 32 bits como REAL *)
```

> **Note:** A ordem parece contraintuitiva. No CODESYS rodando em x86 (little-endian), o elemento `[0]` fica no endereço mais baixo de memória (menos significativo). Como o MK-EM3P envia o high word primeiro, ele vai para `[1]`. Essa é a decodificação correta para o padrão ABCD.

### 2.5 WebVisu — SCADA no Browser

O **WebVisu** é o sistema de visualização web integrado ao CODESYS. Você projeta telas gráficas no IDE e acessa pelo browser em `http://localhost:8080/webvisu.htm`. Os principais elementos que usaremos:

| Elemento         | Uso                                         | Propriedade principal         |
|------------------|---------------------------------------------|-------------------------------|
| Text Field       | Exibir valores numéricos (tensão, corrente) | Format: `%.2f` ou `%d`        |
| Trend            | Gráfico histórico de variáveis              | Time Range, canais coloridos  |
| Input Field      | Digitar um valor (ex: novo TC)              | Ligado a variável GVL         |
| Button           | Executar ação (escrever no PLC)             | OnMouseDown → BOOL variable   |
| Slider           | Ajustar valor visualmente                   | Min/Max, variável REAL/INT    |

---

## 3. Material e Setup

### 3.1 Software necessário

| Software | Versão | Onde baixar |
|----------|--------|-------------|
| CODESYS Development System | 3.5 SP19+ | [https://store.codesys.com/en/codesys.html](https://store.codesys.com/en/codesys.html) (gratuito) |
| CODESYS Control Win SysTray | Incluído no instalador | Mesmo pacote acima |
| ModbusDeviceSIM APK | Última versão | Fornecido pelo professor |

> **Note:** O CODESYS Development System já inclui o SoftPLC para Windows. Durante a instalação, certifique-se de marcar o componente **"CODESYS Control Win SysTray"**.

### 3.2 Pré-requisitos de rede

- Smartphone Android e laptop na **mesma rede Wi-Fi**.
- Você já sabe o **IP do smartphone** (exibido no app após pressionar START).
- `ping <IP_DO_SMARTPHONE>` responde sem perdas de pacote.

### 3.3 Iniciando o simulador no smartphone

1. Abra o **ModbusDeviceSIM**.
2. Selecione **MK-EM3P** no card Device Type.
3. Toque em **START** — o status muda para **RUNNING** em verde.
4. Anote o IP exibido. Exemplo: `192.168.1.42:5020`.
5. Mantenha a tela do smartphone acesa durante toda a prática.

---

## 4. Procedimento

### Parte A — Instalar e Iniciar o CODESYS Control Win SysTray

**A.1** Após instalar o CODESYS Development System, localize o **CODESYS Control Win SysTray** no menu Iniciar do Windows e o inicie.

**A.2** Um ícone verde aparece na **área de notificação** (barra de tarefas, canto inferior direito). Isso indica que o SoftPLC está rodando.

**A.3** Clique com o botão direito no ícone → **Status**. Você verá a versão e o estado atual (`Running` ou `Stopped`).

> **Note:** O SoftPLC precisa estar em execução *antes* de baixar a aplicação. Se o ícone estiver vermelho, clique com o botão direito → **Start PLC**.

---

### Parte B — Criar o Projeto

**B.1** Abra o **CODESYS Development System** (o IDE, não o SysTray).

**B.2** Vá em **File → New Project**.

**B.3** Na janela que abrir, selecione:
- **Standard Project** (não "Empty Project")
- Clique em **OK**.

**B.4** Na janela de seleção do alvo (**Select Target**):
- **Device:** clique na lista suspensa e escolha `CODESYS Control Win SysTray x64`
- **PLC_PRG (Programming Language):** selecione `Structured Text (ST)`
- Clique em **OK**.

**B.5** O projeto é criado com a estrutura base: `MyDevice`, `Application`, `PLC_PRG`.

> **Note:** Se `CODESYS Control Win SysTray x64` não aparecer na lista, o componente não foi instalado corretamente. Reinstale o CODESYS marcando todos os componentes de runtime.

---

### Parte C — Configurar a Árvore de Dispositivos

#### C.1 — Adicionar Ethernet Adapter

**C.1.1** No painel esquerdo **Device Tree**, clique com o botão direito em **MyDevice** → **Add Device**.

**C.1.2** Na janela **Add Device**, expanda a categoria **Fieldbusses** → **Ethernet** → selecione **Ethernet Adapter** → clique em **Add Device**.

**C.1.3** Feche a janela. `Ethernet Adapter` aparece na árvore, abaixo de `MyDevice`.

**C.1.4** Dê duplo clique em **Ethernet Adapter**. No painel direito, em **Interface**, selecione a placa de rede Wi-Fi do laptop (normalmente algo como `Intel(R) Wi-Fi 6...` — a que está na mesma rede do smartphone).

#### C.2 — Adicionar Modbus TCP Master

**C.2.1** Clique com o botão direito em **Ethernet Adapter** → **Add Device**.

**C.2.2** Expanda **Fieldbusses** → **Modbus** → **Modbus TCP** → selecione **Modbus_TCP_Master** → **Add Device**.

#### C.3 — Adicionar Modbus TCP Slave (o MK-EM3P)

**C.3.1** Clique com o botão direito em **Modbus_TCP_Master** → **Add Device**.

**C.3.2** Expanda **Fieldbusses** → **Modbus** → selecione **Modbus_TCP_Slave** → **Add Device**. Feche a janela.

**C.3.3** Dê duplo clique em **Modbus_TCP_Slave** (recém-criado). O painel de configuração abre à direita. Preencha:
- **IP Address:** `192.168.1.42` *(substitua pelo IP real do smartphone)*
- **Port:** `5020`
- **Unit ID:** `1`

**C.3.4** Em **Polling Rate**, deixe `100 ms` (padrão) — o CLP lerá o escravo a cada 100 ms.

> **Note:** O nome do nó na árvore pode ser renomeado. Clique com o botão direito → **Rename** e chame de `EM3P_Slave` para ficar mais legível.

---

### Parte D — Configurar os Canais de Comunicação

Com o nó `Modbus_TCP_Slave` selecionado, clique na aba **Modbus TCP Slave I/O Channels** no painel direito. Você adicionará **4 canais**.

#### Canal 1 — Medições Principais (FC04, regs 0–53)

Clique em **Add Channel** (botão `+`). Configure:

| Campo              | Valor                                |
|--------------------|--------------------------------------|
| Channel Name       | `MeasBlock`                          |
| Access Type        | `Read Input Registers (FC04)`        |
| Register Offset    | `0`                                  |
| Length             | `54`                                 |
| Trigger            | `Cyclic`                             |

> Você já conhece estes registradores do Lab 2: os endereços 0–53 cobrem as 3 tensões (regs 0–5), as 3 correntes (regs 12–17), a potência total (regs 26–27), o fator de potência (regs 50–51) e a frequência (regs 52–53).

#### Canal 2 — Status e Alarmes (FC04, regs 90–91)

Clique em **Add Channel**. Configure:

| Campo              | Valor                                |
|--------------------|--------------------------------------|
| Channel Name       | `StatusBlock`                        |
| Access Type        | `Read Input Registers (FC04)`        |
| Register Offset    | `90`                                 |
| Length             | `2`                                  |
| Trigger            | `Cyclic`                             |

#### Canal 3 — Configuração (FC03, regs 100–103)

Clique em **Add Channel**. Configure:

| Campo              | Valor                                |
|--------------------|--------------------------------------|
| Channel Name       | `ConfigBlock`                        |
| Access Type        | `Read Holding Registers (FC03)`      |
| Register Offset    | `100`                                |
| Length             | `4`                                  |
| Trigger            | `Cyclic`                             |

#### Canal 4 — Escrita do TC Primário (FC06, reg 100)

Clique em **Add Channel**. Configure:

| Campo              | Valor                                              |
|--------------------|----------------------------------------------------|
| Channel Name       | `WriteCT`                                          |
| Access Type        | `Write Single Register (FC06)`                     |
| Register Offset    | `100`                                              |
| Length             | `1`                                                |
| Writable           | `Yes` (marque esta opção se aparecer)              |

> **Note:** Canais de escrita (FC06, FC16) geram variáveis `%QW` (saída), enquanto canais de leitura geram `%IW` (entrada). O CODESYS atribui esses endereços automaticamente conforme você configura os canais.

---

### Parte E — I/O Mapping

Agora você ligará os endereços físicos aos nomes de variáveis do seu programa.

**E.1** Com o nó `Modbus_TCP_Slave` selecionado, clique na aba **Modbus TCP Slave I/O Mapping**.

**E.2** Você verá uma lista de linhas, uma por word (registrador) de cada canal. Cada linha tem uma coluna **Variable** vazia.

**E.3** Para cada linha que precisamos, clique na célula **Variable** e digite o nome da variável GVL que criaremos a seguir. Use a tabela abaixo como referência:

**Canal MeasBlock (inicia em %IW0):**

| Linha | Offset | Endereço | Nome da variável a preencher        |
|-------|--------|----------|--------------------------------------|
| 1     | 0      | %IW0     | `GVL_EM3P.awMeas[0]`                |
| 2     | 1      | %IW1     | `GVL_EM3P.awMeas[1]`                |
| ...   | ...    | ...      | `GVL_EM3P.awMeas[N]`                |
| 54    | 53     | %IW53    | `GVL_EM3P.awMeas[53]`               |

**Canal StatusBlock (inicia em %IW54):**

| Linha | Offset | Endereço | Nome da variável a preencher        |
|-------|--------|----------|--------------------------------------|
| 1     | 0      | %IW54    | `GVL_EM3P.awStatus[0]`              |
| 2     | 1      | %IW55    | `GVL_EM3P.awStatus[1]`              |

**Canal ConfigBlock (inicia em %IW56):**

| Linha | Offset | Endereço | Nome da variável a preencher        |
|-------|--------|----------|--------------------------------------|
| 1     | 0      | %IW56    | `GVL_EM3P.awConfig[0]`              |
| 2     | 1      | %IW57    | `GVL_EM3P.awConfig[1]`              |
| 3     | 2      | %IW58    | `GVL_EM3P.awConfig[2]`              |
| 4     | 3      | %IW59    | `GVL_EM3P.awConfig[3]`              |

**Canal WriteCT (inicia em %QW0 — saída):**

| Linha | Endereço | Nome da variável a preencher        |
|-------|----------|--------------------------------------|
| 1     | %QW0     | `GVL_EM3P.wCTPrimary_Out`           |

> **Note:** Os endereços `%IW` e `%QW` exatos dependem de quantos canais existem antes. O importante é que o I/O Mapping mostre exatamente esses nomes. O CODESYS atribuirá os endereços automaticamente quando você salvar. Se os endereços diferirem, ajuste conforme o mostrado na aba.

---

### Parte F — Criar o Tipo de Dados T_Float32

**F.1** No painel esquerdo, clique com o botão direito em **Application** → **Add Object** → **DUT (Data Unit Type)**.

**F.2** Na janela, escolha:
- **Name:** `T_Float32`
- **Type:** `UNION`
- Clique em **Add**.

**F.3** O editor de texto abre. Substitua todo o conteúdo pelo código abaixo:

```iecst
TYPE T_Float32 :
UNION
    arWord : ARRAY[0..1] OF WORD;
    rValue : REAL;
END_UNION
END_TYPE
```

**F.4** Pressione **Ctrl+S** para salvar.

> **Note:** O tipo `T_Float32` é a chave para converter os dois words brutos do Modbus em um número real. Você usará uma variável deste tipo para cada grandeza a decodificar.

---

### Parte G — Criar a GVL_EM3P (Lista de Variáveis Globais)

**G.1** No painel esquerdo, clique com o botão direito em **Application** → **Add Object** → **Global Variable List (GVL)**.

**G.2** Na janela, defina:
- **Name:** `GVL_EM3P`
- Clique em **Add**.

**G.3** Substitua o conteúdo pelo código abaixo:

```iecst
VAR_GLOBAL
    (* --- Arrays brutos do I/O Mapping --- *)
    awMeas    : ARRAY[0..53] OF WORD;   (* Canal MeasBlock: FC04 regs 0–53 *)
    awStatus  : ARRAY[0..1]  OF WORD;   (* Canal StatusBlock: FC04 regs 90–91 *)
    awConfig  : ARRAY[0..3]  OF WORD;   (* Canal ConfigBlock: FC03 regs 100–103 *)
    wCTPrimary_Out : WORD;               (* Canal WriteCT: FC06 reg 100 — saída *)

    (* --- Valores decodificados (REAL) --- *)
    rVoltageL1  : REAL;   (* Tensão L1-N [V] *)
    rVoltageL2  : REAL;   (* Tensão L2-N [V] *)
    rVoltageL3  : REAL;   (* Tensão L3-N [V] *)
    rCurrentL1  : REAL;   (* Corrente L1  [A] *)
    rCurrentL2  : REAL;   (* Corrente L2  [A] *)
    rCurrentL3  : REAL;   (* Corrente L3  [A] *)
    rActivePower : REAL;  (* Potência Ativa Total [kW] *)
    rPowerFactor : REAL;  (* Fator de Potência Total *)
    rFrequency  : REAL;   (* Frequência [Hz] *)

    (* --- Status --- *)
    wAlarmStatus  : WORD;  (* Reg 90: bitmask de alarmes *)
    wDeviceStatus : WORD;  (* Reg 91: status do dispositivo *)

    (* --- Configuração lida --- *)
    wCTPrimary_Read : WORD;   (* Reg 100 lido: TC Primário [A] *)
    wVTPrimary_Read : WORD;   (* Reg 102 lido: TP Primário [V] *)

    (* --- Controle da interface WebVisu --- *)
    wCTPrimary_New  : WORD  := 100;   (* valor digitado pelo operador *)
    bWriteCT        : BOOL;            (* botão "Escrever TC" *)
END_VAR
```

**G.4** Pressione **Ctrl+S**.

---

### Parte H — Programar o PLC_PRG em Structured Text

**H.1** No painel esquerdo, dê duplo clique em **PLC_PRG** para abrir o editor ST.

**H.2** Substitua todo o conteúdo pelo código abaixo:

```iecst
PROGRAM PLC_PRG
VAR
    (* UNION para decodificação FLOAT32 — reutilizada para cada cálculo *)
    uF : T_Float32;
END_VAR
```

No **corpo do programa** (área abaixo da seção VAR), adicione:

```iecst
(* ========================================================
   DECODIFICAÇÃO DAS MEDIÇÕES (FC04, regs 0–53)
   Padrão ABCD: high word → arWord[1], low word → arWord[0]
   ======================================================== *)

(* Tensão L1-N — registradores 0 (high) e 1 (low) *)
uF.arWord[1] := GVL_EM3P.awMeas[0];
uF.arWord[0] := GVL_EM3P.awMeas[1];
GVL_EM3P.rVoltageL1 := uF.rValue;

(* Tensão L2-N — registradores 2 (high) e 3 (low) *)
uF.arWord[1] := GVL_EM3P.awMeas[2];
uF.arWord[0] := GVL_EM3P.awMeas[3];
GVL_EM3P.rVoltageL2 := uF.rValue;

(* Tensão L3-N — registradores 4 (high) e 5 (low) *)
uF.arWord[1] := GVL_EM3P.awMeas[4];
uF.arWord[0] := GVL_EM3P.awMeas[5];
GVL_EM3P.rVoltageL3 := uF.rValue;

(* Corrente L1 — registradores 12 (high) e 13 (low) *)
uF.arWord[1] := GVL_EM3P.awMeas[12];
uF.arWord[0] := GVL_EM3P.awMeas[13];
GVL_EM3P.rCurrentL1 := uF.rValue;

(* Corrente L2 — registradores 14 (high) e 15 (low) *)
uF.arWord[1] := GVL_EM3P.awMeas[14];
uF.arWord[0] := GVL_EM3P.awMeas[15];
GVL_EM3P.rCurrentL2 := uF.rValue;

(* Corrente L3 — registradores 16 (high) e 17 (low) *)
uF.arWord[1] := GVL_EM3P.awMeas[16];
uF.arWord[0] := GVL_EM3P.awMeas[17];
GVL_EM3P.rCurrentL3 := uF.rValue;

(* Potência Ativa Total — registradores 26 (high) e 27 (low) *)
uF.arWord[1] := GVL_EM3P.awMeas[26];
uF.arWord[0] := GVL_EM3P.awMeas[27];
GVL_EM3P.rActivePower := uF.rValue;

(* Fator de Potência Total — registradores 50 (high) e 51 (low) *)
uF.arWord[1] := GVL_EM3P.awMeas[50];
uF.arWord[0] := GVL_EM3P.awMeas[51];
GVL_EM3P.rPowerFactor := uF.rValue;

(* Frequência — registradores 52 (high) e 53 (low) *)
uF.arWord[1] := GVL_EM3P.awMeas[52];
uF.arWord[0] := GVL_EM3P.awMeas[53];
GVL_EM3P.rFrequency := uF.rValue;

(* ========================================================
   STATUS E ALARMES (FC04, regs 90–91)
   ======================================================== *)
GVL_EM3P.wAlarmStatus  := GVL_EM3P.awStatus[0];   (* reg 90 *)
GVL_EM3P.wDeviceStatus := GVL_EM3P.awStatus[1];   (* reg 91 *)

(* ========================================================
   CONFIGURAÇÃO LIDA (FC03, regs 100–103)
   Reg 100 = CT Primary (UINT16, sem float)
   Reg 102 = VT Primary (UINT16, sem float)
   ======================================================== *)
GVL_EM3P.wCTPrimary_Read := GVL_EM3P.awConfig[0];   (* reg 100 *)
GVL_EM3P.wVTPrimary_Read := GVL_EM3P.awConfig[2];   (* reg 102 *)

(* ========================================================
   ESCRITA DO TC PRIMÁRIO (FC06, reg 100)
   O botão bWriteCT na WebVisu sinaliza a escrita.
   Copiamos o valor digitado pelo operador para a saída %QW.
   ======================================================== *)
IF GVL_EM3P.bWriteCT THEN
    GVL_EM3P.wCTPrimary_Out := GVL_EM3P.wCTPrimary_New;
    GVL_EM3P.bWriteCT := FALSE;   (* auto-reset após um ciclo *)
END_IF
```

**H.3** Pressione **Ctrl+S**.

> **Note:** Os comentários `(* ... *)` são parte do estilo de programação IEC 61131-3. Mantenha-os no seu código — eles são avaliados na nota de entregáveis.

---

### Parte I — Criar a Interface WebVisu

#### I.1 — Adicionar a WebVisu ao projeto

**I.1.1** No painel esquerdo, clique com o botão direito em **Application** → **Add Object** → **Visualization**.

**I.1.2** Na janela, configure:
- **Name:** `EM3P_Screen`
- Marque a opção **"Use as WebVisu"** ou **"Target Visualization"** (o nome pode variar conforme versão).
- Clique em **Add**.

**I.1.3** O editor visual abre com uma área de canvas em branco.

#### I.2 — Configurar o WebVisu Server (se necessário)

**I.2.1** No painel esquerdo, clique com o botão direito em **Application** → **Add Object** → **WebVisu** (se não aparecer automaticamente, vá em **Tools → Update Device Description**).

**I.2.2** Dê duplo clique no nó **WebVisu** e confirme que o **Port** está em `8080`.

#### I.3 — Adicionar Text Fields para as medições

No editor visual da `EM3P_Screen`, adicione 6 Text Fields. Para cada um:

1. Na paleta de objetos (barra lateral direita), arraste um **Text Field** para o canvas.
2. Dê duplo clique no objeto → aba **Text** → defina o texto estático e o **Format**:
   - Exemplo para Tensão L1: texto estático `Tensão L1-N:`, format `%.2f V`
3. Aba **Variable** (ou clique em **...** no campo Variable) → selecione a variável GVL:
   - Tensão L1: `GVL_EM3P.rVoltageL1`
4. Repita para os 6 campos:

| Rótulo visível       | Variável GVL              | Format      |
|----------------------|---------------------------|-------------|
| Tensão L1-N          | `GVL_EM3P.rVoltageL1`     | `%.2f V`    |
| Tensão L2-N          | `GVL_EM3P.rVoltageL2`     | `%.2f V`    |
| Tensão L3-N          | `GVL_EM3P.rVoltageL3`     | `%.2f V`    |
| Corrente L1          | `GVL_EM3P.rCurrentL1`     | `%.2f A`    |
| Potência Ativa Total | `GVL_EM3P.rActivePower`   | `%.3f kW`   |
| Frequência           | `GVL_EM3P.rFrequency`     | `%.2f Hz`   |

> **Note:** No Text Field do CODESYS, o **Format** funciona como `printf` do C. `%.2f` exibe 2 casas decimais. `%d` exibe inteiro. Certifique-se de que a variável ligada é `REAL` quando usar `%f`, ou `WORD`/`INT` quando usar `%d`.

#### I.4 — Adicionar um Elemento Trend (gráfico histórico)

**I.4.1** Na paleta, arraste um **Trend** (ou **Trend Recorder**) para o canvas. Redimensione para ocupar boa parte da tela.

**I.4.2** Dê duplo clique no Trend → aba **Channels** (ou **Variables**):
- Clique em **Add** → variável: `GVL_EM3P.rVoltageL1` → cor: **Azul** → rótulo: `V L1-N`
- Clique em **Add** → variável: `GVL_EM3P.rActivePower` → cor: **Vermelho** → rótulo: `P Ativa (kW)`

**I.4.3** Aba **Axis** (ou **Time Range**):
- **Time Range:** `60 s` (mostra o último minuto)
- **Y Range Auto Scale:** marque esta opção para o eixo Y se ajustar automaticamente.

> Você terá agora um gráfico que vai crescendo à direita conforme o tempo passa — exatamente como um sistema SCADA industrial.

#### I.5 — Adicionar Input Field para o TC Primário

**I.5.1** Arraste um **Text Field** ou **Input Field** para o canvas.

**I.5.2** Configure:
- Rótulo estático: `TC Primário (A):`
- Variável: `GVL_EM3P.wCTPrimary_New`
- Format: `%d`
- **Habilitado para edição:** marque "Write access" ou "Editable = YES" (dependendo da versão do CODESYS, pode ser um "Input Text Field" separado na paleta).

> O operador clicará neste campo na WebVisu, digitará um valor (ex: `200`) e pressionará Enter. O valor é gravado na variável `wCTPrimary_New` no PLC.

#### I.6 — Adicionar Botão "Escrever TC"

**I.6.1** Arraste um **Button** para o canvas.

**I.6.2** Dê duplo clique → aba **Text**: escreva `ESCREVER TC`.

**I.6.3** Aba **Input** (ou **Mouse Actions**):
- **OnMouseDown:** `SetVar` → variável: `GVL_EM3P.bWriteCT` → valor: `TRUE`

> Quando o operador clicar no botão, `bWriteCT` vai a `TRUE`, e na próxima varredura do PLC o código ST copia `wCTPrimary_New` para `wCTPrimary_Out` (que vai para o canal FC06 → MK-EM3P).

#### I.7 — Adicionar Texto de Status (opcional, recomendado)

Adicione mais um Text Field para exibir o status de alarme:
- Rótulo: `Alarm Status:`
- Variável: `GVL_EM3P.wAlarmStatus`
- Format: `0x%04X` *(exibe em hexadecimal, facilita leitura do bitmask)*

---

### Parte J — Download, Runtime e Acesso WebVisu

#### J.1 — Compilar o projeto

**J.1.1** Vá em **Build → Build** (ou pressione **F11**).

**J.1.2** Verifique a aba **Messages** (parte inferior do IDE). Não deve haver erros. Avisos (*warnings*) são aceitáveis se forem sobre variáveis não usadas.

> **Note:** Erros comuns nesta etapa: variável usada no I/O Mapping mas não declarada na GVL (crie-a), tipo incompatível entre WORD e REAL (reveja o código ST).

#### J.2 — Conectar ao SoftPLC e baixar a aplicação

**J.2.1** Vá em **Online → Login** (ou **Alt+F8**). O CODESYS buscará o SoftPLC rodando localmente.

**J.2.2** Se uma janela perguntar "A aplicação existe mas difere. Fazer download?", clique em **Yes**.

**J.2.3** Após o login, a barra de status no rodapé mostra o estado do PLC.

**J.2.4** Vá em **Debug → Start** (ou **F5**) para iniciar a execução da aplicação.

#### J.3 — Verificar comunicação Modbus

**J.3.1** No painel esquerdo, dê duplo clique no nó `EM3P_Slave`. Abra a aba **Status** ou **Diagnosis**.

**J.3.2** O contador **Successful Requests** deve estar aumentando. Se **Errors** crescer, verifique IP e porta.

**J.3.3** Dê duplo clique em **GVL_EM3P** → os valores dos campos `awMeas[0]`, `awMeas[1]`, etc. devem aparecer como números (não zero). Se aparecer tudo zero, a comunicação não está funcionando.

#### J.4 — Abrir o WebVisu no browser

**J.4.1** Abra o **Google Chrome** (recomendado) ou qualquer browser.

**J.4.2** Acesse: `http://localhost:8080/webvisu.htm`

**J.4.3** A tela `EM3P_Screen` deve aparecer com os valores atualizando em tempo real.

**J.4.4** Verifique:
- Tensão L1-N mostrando ~220 V (±5%)
- Frequência mostrando ~60 Hz
- Gráfico Trend com as curvas em movimento

#### J.5 — Testar a escrita do TC Primário

**J.5.1** No WebVisu, clique no Input Field **TC Primário (A)**.

**J.5.2** Apague o valor atual e digite `200`. Pressione Enter.

**J.5.3** Clique no botão **ESCREVER TC**.

**J.5.4** No CODESYS IDE, vá em **Online → Watch Variables** e observe `GVL_EM3P.wCTPrimary_Read`. Após alguns ciclos, deve mudar para `200`.

**J.5.5** No smartphone, veja o visor LCD do MK-EM3P. A página de configuração deve exibir `CT: 200 A`.

> Você acaba de fechar o ciclo completo: **WebVisu → PLC → Modbus TCP → Dispositivo de Campo**. Este é o fluxo real de um sistema SCADA industrial.

---

## 5. Critérios de Sucesso

Você completou esta prática se:

- ✅ **C1 — Comunicação estabelecida:** a aba Status/Diagnosis do nó `EM3P_Slave` mostra `Successful Requests` crescendo sem erros.
- ✅ **C2 — Decodificação correta:** os valores `rVoltageL1`, `rVoltageL2`, `rVoltageL3` exibidos na Watch Table do IDE são flutuantes na faixa de 210–230 V.
- ✅ **C3 — Frequência:** `rFrequency` exibe valor próximo a 60 Hz (± 1 Hz).
- ✅ **C4 — WebVisu acessível:** a URL `http://localhost:8080/webvisu.htm` abre no browser com os campos numéricos atualizando em tempo real.
- ✅ **C5 — Escrita funcional:** após digitar `200` no Input Field e clicar em ESCREVER TC, o campo `TC Primário` lido no app do smartphone muda para 200 A em até 3 segundos.

---

## 6. Discussão e Reflexão

Responda no relatório:

1. **Conceitual.** Na Parte H, o código ST usa `uF.arWord[1]` para o *high word* e `uF.arWord[0]` para o *low word*. Por que não é o contrário? O que mudaria se o dispositivo usasse ordem **CDAB** (little-endian por word)?

2. **Comparativo.** No **Lab 2 (EasyModbusTCP)**, você leu os mesmos registradores manualmente. No CODESYS, a leitura é cíclica e automática. Quais são as vantagens e limitações de cada abordagem para uso em produção em uma planta real?

3. **Diagnóstico.** Imagine que `rFrequency` exibe `0.0` enquanto `rVoltageL1` exibe corretamente 220 V. Qual seria a causa mais provável? Quais passos você seguiria para investigar?

4. **Aplicação.** O botão ESCREVER TC usa `bWriteCT := TRUE` e o PLC faz `bWriteCT := FALSE` no mesmo ciclo. Por que é importante este auto-reset? O que aconteceria se o código ST não zerasse a variável?

5. **Expansão.** Com base no que você aprendeu, como você adicionaria a leitura de **Alarm Status** (bitmask de 8 bits) ao WebVisu, com cada bit exibindo um LED colorido (verde = sem alarme, vermelho = alarme ativo)?

---

## 7. Entregáveis

Submeta um único arquivo PDF contendo:

1. **Screenshot do Device Tree** completo com os 4 canais configurados e visíveis.
2. **Screenshot da I/O Mapping** com pelo menos 10 linhas preenchidas com nomes de variáveis.
3. **Código completo do PLC_PRG** (copie o texto do editor ST — não fotografe a tela).
4. **Screenshot do WebVisu** no browser mostrando pelo menos os 6 campos de medição com valores reais.
5. **Screenshot do Watch Table** do CODESYS IDE com `rVoltageL1`, `rFrequency` e `wCTPrimary_Read` visíveis com valores não nulos.
6. **Screenshot do smartphone** confirmando a mudança do TC Primário para 200 A.
7. **Respostas às 5 perguntas** da Seção 6, com no mínimo 4 linhas cada.

---

*Prática elaborada por **Mekatronik — Advanced Engineering** para o curso de Comunicações Industriais.*
*Prof. Dênis Leite — Laboratório de Automação Industrial.*
