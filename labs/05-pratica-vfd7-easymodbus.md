# Prática 4 — MK-VFD7 com EasyModbusTCP

> *"Comande um motor pela rede — e entenda por que isso muda tudo."*

## 1. Contexto Industrial

Inversores de frequência (também chamados de **VFDs** — Variable Frequency Drives, ou **drives**) são onipresentes na indústria. Eles controlam **velocidade, torque e direção** de motores trifásicos, e estão presentes em **esteiras, bombas, ventiladores, elevadores, compressores** — praticamente qualquer máquina rotativa moderna.

Marcas como **WEG**, **ABB**, **Siemens**, **Danfoss**, **Schneider** oferecem comunicação **Modbus TCP** em todos os seus inversores médios e grandes. Pelo Modbus, um CLP ou supervisório pode:

- **Comandar** start, stop, reverse, jog
- **Definir** referência de velocidade
- **Monitorar** velocidade real, corrente, potência, temperatura
- **Configurar** parâmetros (tempo de aceleração, frequência máxima, etc.)
- **Diagnosticar** falhas

Nesta prática, você irá controlar um **inversor simulado** (MK-VFD7) e entender a estrutura do **Control Word** e do **Status Word** — dois conceitos universais em qualquer inversor.

---

## 2. Conceitos Necessários

### 2.1 Control Word (Palavra de Controle)

É um **registrador UINT16** onde **cada bit é um comando**. No MK-VFD7 está no endereço **100**.

| Bit | Máscara | Significado          |
|-----|---------|----------------------|
| 0   | 0x0001  | RUN (1 = rodar)      |
| 1   | 0x0002  | REVERSE direção      |
| 2   | 0x0004  | JOG                  |
| 3   | 0x0008  | Fault Reset          |
| 4   | 0x0010  | E-Stop (parada de emergência) |

**Combinações comuns:**

| Valor | Bits ligados | Ação                  |
|-------|-------------|------------------------|
| `0`   | nenhum      | Stop                   |
| `1`   | bit 0       | Run forward            |
| `3`   | bits 0+1    | Run reverse            |
| `5`   | bits 0+2    | Jog forward            |
| `16`  | bit 4       | Emergency stop         |

### 2.2 Status Word (Palavra de Status)

Análoga, mas **read-only**. No MK-VFD7 está no endereço **26** (Input Register, FC04).

| Bit | Máscara | Significado          |
|-----|---------|----------------------|
| 0   | 0x0001  | Running              |
| 1   | 0x0002  | Forward              |
| 2   | 0x0004  | Reverse              |
| 3   | 0x0008  | At reference         |
| 4   | 0x0010  | Accelerating         |
| 5   | 0x0020  | Decelerating         |
| 6   | 0x0040  | Fault active         |

### 2.3 Modo LOCAL vs. REMOTE

> **⚠ Atenção crítica:** o MK-VFD7 tem dois modos:
> - **LOCAL**: controle pelos botões do painel do app. Comandos via Modbus são **ignorados**.
> - **REMOTE**: controle via Modbus. Os botões locais ficam desabilitados.
>
> **Para esta prática, certifique-se de que o modo está em REMOTE.** No app, há um switch LOCAL/REMOTE no painel.

### 2.4 Mapa de Registradores do MK-VFD7

**Medições (FC04 — Input Registers):**

| Endereço | Variável         | Tipo    | Unidade |
|----------|------------------|---------|---------|
| 0–1      | Output Frequency | FLOAT32 | Hz      |
| 2–3      | Output Voltage   | FLOAT32 | V       |
| 4–5      | Output Current   | FLOAT32 | A       |
| 6–7      | Output Power     | FLOAT32 | kW      |
| 8–9      | Motor Speed      | FLOAT32 | RPM     |
| 10–11    | Motor Torque     | FLOAT32 | %       |
| 12–13    | DC Bus Voltage   | FLOAT32 | V       |
| 14–15    | Drive Temperature| FLOAT32 | °C      |
| 26       | Drive Status     | UINT16  | bitmask |
| 27       | Fault Code       | UINT16  | número  |
| 28       | Warning Code     | UINT16  | número  |

**Controle e Configuração (FC03/FC06/FC16 — Holding Registers):**

| Endereço | Variável             | Tipo    | Default |
|----------|----------------------|---------|---------|
| 100      | Control Word         | UINT16  | 0       |
| 101–102  | Frequency Reference  | FLOAT32 | 30.0 Hz |
| 103–104  | Acceleration Time    | FLOAT32 | 10.0 s  |
| 105–106  | Deceleration Time    | FLOAT32 | 10.0 s  |
| 107–108  | Max Frequency        | FLOAT32 | 60.0 Hz |

---

## 3. Material Necessário

- 1 **smartphone Android** com **ModbusDeviceSIM** instalado
- 1 **laptop** com **EasyModbusTCP** instalado
- Conexão Wi-Fi compartilhada

---

## 4. Setup Inicial

### 4.1 No smartphone

1. Abra o **ModbusDeviceSIM**.
2. No card **Device Type**, toque em **MK-VFD7** *(diferente da prática 1!)*.
3. Toque em **START**.
4. **Aguarde o app inicializar** (~2 segundos).
5. **Encontre o switch LOCAL/REMOTE** no painel do app. **Coloque em REMOTE.**
   - Se estiver em **LOCAL** (amarelo), seus comandos Modbus serão ignorados.
6. Anote o IP (ex.: `192.168.0.107:5020`).

### 4.2 No laptop

1. Verifique conectividade: `ping <IP_smartphone>`.
2. Abra **EasyModbusTCP**.

---

## 5. Procedimento

### Etapa 1 — Conectar

Em EasyModbusTCP:
- **IP**: `<IP do smartphone>`
- **Port**: `5020`
- **Unit ID**: `1`

Clique **Connect**. Confirme no app que `Clients = 1`.

---

### Etapa 2 — Estado Inicial: Drive Parado

Leia o **Drive Status** (registrador 26, FC04):

- **Start Address**: `26`
- **Number of Inputs**: `3`
- **Function**: FC04

Você deve ver:
- Reg 26 = `0` (status = parado, sem nenhum bit ligado)
- Reg 27 = `0` (sem falha)
- Reg 28 = `0` (sem warning)

Leia também a **Output Frequency** (regs 0–1, FC04). Deve ser ~`0.0 Hz`.

---

### Etapa 3 — Configurar a Frequência de Referência

Vamos definir o setpoint de velocidade para **45 Hz**.

**3.1.** Converta `45.0` em IEEE 754:
- 45.0 = `0x42340000` = **(0x4234, 0x0000)** = **(16948, 0)** em decimal

**3.2.** Em EasyModbusTCP, vá para **Write Multiple Registers (FC16)**:
- **Start Address**: `101`
- **Number of Registers**: `2`
- **Values**: `16948, 0`

Clique **Write**.

**3.3.** Verifique lendo de volta:
- FC03, Start `101`, Inputs `2`.
- Deve mostrar `16948, 0`.

✓ **Frequência de referência configurada.**

---

### Etapa 4 — Comandar START

Agora envie o comando de partida:

**4.1.** Em **Write Single Register (FC06)**:
- **Register Address**: `100` (Control Word)
- **Value**: `1` (bit 0 = RUN)

Clique **Write**.

**4.2.** Observe imediatamente:
- **No smartphone:** o LED **RUN** acende em verde. O LCD começa a mostrar a frequência subindo (`5.0`, `10.0`, `15.0`...). A indicação **ACC** (acelerando) acende.
- **Após ~10 segundos:** a frequência estabiliza em 45.0 Hz e o LED **AT REF** (em referência) acende.

**4.3.** Leia o Output Frequency a cada poucos segundos (FC04, regs 0–1). Decodifique o FLOAT32 e veja como o valor sobe gradualmente.

**4.4.** Leia o **Drive Status** (FC04, reg 26):
- Quando rodando, deve mostrar valor em hex como `0x000B` = 11 decimal (bits 0, 1, 3 ligados — Running, Forward, At Reference).
- Use a calculadora ou olhe os bits no app.

---

### Etapa 5 — Mudar para REVERSE

Enquanto o drive está rodando em 45 Hz forward:

**5.1.** Envie Control Word = `3` (RUN + REVERSE):
- FC06, Reg 100, Value `3`.

**5.2.** Observe:
- Frequência cai gradualmente para 0 (LED DEC acende).
- Quando atinge 0, muda para REVERSE.
- Frequência sobe novamente para 45 Hz, agora no sentido oposto.
- LED REV (vermelho/laranja) acende; LED FWD apaga.

**5.3.** Leia o Drive Status. Agora deve mostrar bits 0, 2 ligados (Running, Reverse).

---

### Etapa 6 — Mudar a Frequência em Operação

Com o drive ainda rodando (em reverse):

**6.1.** Escreva nova frequência de referência: **25.0 Hz** = `0x41C80000` = **(0x41C8, 0x0000)** = `(16840, 0)`:
- FC16, Start 101, Qty 2, Values `16840, 0`.

**6.2.** Observe: o drive desacelera (LED DEC) e estabiliza em 25 Hz.

**6.3.** Verifique no smartphone: o LCD do app mostra a nova frequência.

---

### Etapa 7 — STOP

Envie comando de parada:

**7.1.** Control Word = `0`:
- FC06, Reg 100, Value `0`.

**7.2.** Observe: o drive desacelera para 0, LED RUN apaga.

---

### Etapa 8 — Modificar Acceleration Time

A aceleração padrão é 10 s. Vamos mudar para 3 s (aceleração mais rápida).

**8.1.** Converta 3.0 em FLOAT32:
- 3.0 = `0x40400000` = `(0x4040, 0x0000)` = `(16448, 0)`

**8.2.** Escreva no endereço 103:
- FC16, Start 103, Qty 2, Values `16448, 0`.

**8.3.** Confirme com FC03, Start 103, Inputs 2.

**8.4.** Reinicie o drive com Control Word = 1 e observe que ele atinge 25 Hz **muito mais rápido**.

**8.5.** Pare novamente (Control Word = 0).

---

### Etapa 9 — Simular uma Condição de Falha (opcional)

O simulador permite provocar algumas falhas via configurações inadequadas. Tente:

**9.1.** Reduza a Max Frequency para 20 Hz:
- 20.0 = `0x41A00000` = `(16800, 0)`
- FC16, Start 107, Qty 2, Values `16800, 0`.

**9.2.** Configure Frequency Reference = 50 Hz (acima do máximo):
- 50.0 = `0x42480000` = `(16968, 0)`
- FC16, Start 101, Qty 2, Values `16968, 0`.

**9.3.** Tente RUN. O drive deve apresentar comportamento limitado ou warning.

**9.4.** Leia o **Warning Code** (reg 28, FC04). Diferente de 0 indica warning ativo.

**9.5.** Restaure Max Frequency = 60 Hz para limpar.

---

### Etapa 10 — Voltar ao Estado Inicial

Antes de finalizar:

- Control Word = `0` (parar)
- Frequency Reference = `30.0` Hz (default) = `(0x41F0, 0x0000)` = `(16880, 0)`
- Acceleration Time = `10.0` s = `(0x4120, 0x0000)` = `(16672, 0)`
- Max Frequency = `60.0` Hz = `(0x4270, 0x0000)` = `(17008, 0)`

---

## 6. Critérios de Sucesso

Você completou esta prática se conseguiu:

- ✅ Conectar EasyModbusTCP ao MK-VFD7 (Clients = 1 no app).
- ✅ Configurar Frequency Reference como FLOAT32 (Etapa 3).
- ✅ Iniciar o drive (Control Word = 1) e ver a frequência subindo (Etapa 4).
- ✅ Mudar para reverse (Control Word = 3) e ver a inversão (Etapa 5).
- ✅ Alterar Frequency Reference em operação (Etapa 6).
- ✅ Parar o drive (Control Word = 0) (Etapa 7).
- ✅ Modificar Acceleration Time e observar mudança no comportamento (Etapa 8).
- ✅ Ler e interpretar **Drive Status Word** corretamente em pelo menos 3 estados diferentes (parado, rodando forward, rodando reverse).

---

## 7. Discussão e Reflexão

1. **Conceitual.** Por que o Control Word é um **bitmask** em vez de campos separados? Quais as vantagens dessa abordagem?
2. **Análise.** Capture o Drive Status Word em 3 momentos: parado, acelerando, e em referência (rodando estável). Decodifique cada bit em uma tabela.
3. **Segurança.** Em uma planta real, o que aconteceria se um cliente Modbus enviasse repetidamente Control Word = 1 sem coordenação? Por que o modo LOCAL/REMOTE existe?
4. **Diagnóstico.** Suponha que você envia RUN (Control Word = 1) mas o drive não inicia. Liste 4 possíveis causas e como verificá-las.
5. **Aplicação.** Em uma esteira transportadora, o operador precisa poder parar a esteira **imediatamente** em caso de emergência. Como você implementaria isso usando os bits do Control Word?
6. **Reflexão.** Por que, em VFDs reais, o **Fault Reset** geralmente requer um **transição de borda** (bit subindo de 0 para 1) em vez de apenas o bit estar em 1?

---

## 8. Entregáveis para Avaliação

Submeta:

1. **Capturas de tela** do EasyModbusTCP mostrando:
   - Conexão (Clients = 1)
   - Configuração da frequência de referência
   - Drive em operação (Status ≠ 0)
   - Drive parado novamente
2. **Capturas do smartphone** mostrando:
   - LED RUN aceso durante operação
   - Painel LCD mostrando frequência durante aceleração
   - Indicador FWD vs. REV
3. **Tabela decodificada do Drive Status Word** em 3 momentos diferentes.
4. **Tabela de valores hex/decimal** que você escreveu nos registradores ao longo da prática (referência da frequência, control word, etc.).
5. **Respostas** às 6 perguntas da seção 7.

---

## 9. Solução de Problemas Específicos

| Sintoma | Causa | Solução |
|---------|-------|---------|
| Control Word = 1, mas nada acontece | App em modo LOCAL | Coloque em REMOTE no painel do app |
| Drive inicia mas para imediatamente | E-Stop ativo (bit 4) | Control Word = 0, depois 1 |
| Frequência fica em 0 | Frequency Reference = 0 ou abaixo do mínimo | Configure ref > 0.5 Hz |
| Frequência limitada | Max Frequency baixa | Confirme reg 107-108 = 60.0 |
| LED Fault aceso | Fault code ≠ 0 | Fault Reset: Control Word = 8, depois 0 |
| Comandos parecem aleatórios | Reg 100 vs reg 101 confundidos | Control Word = endereço 100 |

---

## 10. Próximos Passos

- **[Prática 5 — VFD7 com Python](06-pratica-vfd7-python.md)**: automatize sequências de partida.
- **[Prática 6 — VFD7 com Node-RED](07-pratica-vfd7-nodered.md)**: construa uma HMI completa.

---

**Bom controle!**
