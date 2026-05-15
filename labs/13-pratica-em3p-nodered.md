# Prática 3 — MK-EM3P com Node-RED

> *"Dashboard, histórico e controle — tudo em um fluxo visual."*

## 1. Contexto Industrial

**Node-RED** é uma plataforma low-code que se tornou padrão para integração industrial moderna. Empresas como Schneider Electric, Siemens, ABB e Rockwell oferecem distribuições próprias do Node-RED. É usado para:

- **Conectar** sistemas heterogêneos (Modbus, MQTT, REST, OPC UA, bancos de dados, nuvem).
- **Criar dashboards** em minutos, sem precisar programar interface gráfica.
- **Implementar lógica** de processamento usando blocos visuais e snippets de JavaScript.
- **Persistir dados** localmente ou em nuvem.

Nesta prática, você implementará um **sistema completo de monitoramento** do medidor de energia MK-EM3P com:

- Leitura periódica e visualização em tempo real (gauges, gráficos)
- Histórico persistente em arquivo CSV
- Painel de alarmes
- Interface para alterar parâmetros de configuração

Este é o tipo de aplicação que substitui SCADAs caros em pequenas e médias plantas, e o tipo de habilidade muito requisitada no mercado atual.

---

## 2. Conceitos Necessários

### 2.1 Conceitos do Node-RED

| Conceito       | O que é                                                            |
|---------------|---------------------------------------------------------------------|
| **Fluxo (flow)** | Conjunto conectado de nodes que processam dados                  |
| **Node**       | Bloco visual que faz uma tarefa (ler Modbus, calcular, exibir gauge) |
| **Wire**       | Linha que conecta a saída de um node à entrada de outro            |
| **`msg`**       | Objeto que passa entre nodes; contém `msg.payload` e outros campos  |
| **Dashboard**  | Conjunto de widgets (gauge, chart, button) acessível via navegador  |
| **Function node** | Permite escrever JavaScript para transformar `msg.payload`     |
| **Inject node** | Dispara o fluxo periodicamente ou sob demanda                     |
| **Switch node** | Roteia mensagens conforme uma condição                            |

### 2.2 Decodificação FLOAT32 em JavaScript

```javascript
// Combina 2 registradores Modbus (ABCD) em um float
function wordsToFloat(high, low) {
    const buffer = Buffer.alloc(4);
    buffer.writeUInt16BE(high, 0);
    buffer.writeUInt16BE(low, 2);
    return buffer.readFloatBE(0);
}
```

### 2.3 Mapa de registradores

Resumo dos principais (todos via FC04 — Read Input Registers):

| Endereço | Variável              | Tipo    |
|----------|-----------------------|---------|
| 0–1      | Voltage L1-N          | FLOAT32 |
| 2–3      | Voltage L2-N          | FLOAT32 |
| 4–5      | Voltage L3-N          | FLOAT32 |
| 12–13    | Current L1            | FLOAT32 |
| 14–15    | Current L2            | FLOAT32 |
| 16–17    | Current L3            | FLOAT32 |
| 26–27    | Active Power Total    | FLOAT32 |
| 50–51    | Power Factor Total    | FLOAT32 |
| 52–53    | Frequency             | FLOAT32 |
| 90       | Alarm Status (bitmask)| UINT16  |

E para configuração (FC03 — Holding Registers):

| Endereço | Variável               | Tipo    |
|----------|------------------------|---------|
| 100      | CT Primary             | UINT16  |
| 107–108  | Over-Voltage Threshold | FLOAT32 |

---

## 3. Material Necessário

- 1 **smartphone Android** com **ModbusDeviceSIM** instalado
- 1 **laptop** com:
  - **Node.js 18+** instalado (verifique: `node --version`)
  - **Node-RED** instalado (vamos cobrir a instalação)
  - Navegador moderno
- Conexão Wi-Fi compartilhada

---

## 4. Setup Inicial

### 4.1 No smartphone

1. Abra o **ModbusDeviceSIM**.
2. Selecione **MK-EM3P**.
3. Toque em **START**.
4. Anote o IP exibido (ex.: `192.168.0.105:5020`).

### 4.2 No laptop — Instalar Node-RED

```bash
# Instale globalmente
npm install -g --unsafe-perm node-red

# Inicie
node-red
```

Você verá no terminal:

```
Welcome to Node-RED
===================
12 May 19:32:14 - [info] Node-RED version: v3.x.x
12 May 19:32:14 - [info] Node.js version: v18.x.x
...
12 May 19:32:15 - [info] Server now running at http://127.0.0.1:1880/
```

**Mantenha esse terminal aberto** durante toda a prática.

### 4.3 Abra a interface

No navegador, vá para:

```
http://localhost:1880
```

Você verá o editor de fluxos do Node-RED.

### 4.4 Instale os módulos necessários

No menu superior direito (≡) → **Manage palette** → aba **Install**:

Instale os seguintes pacotes:

1. **`node-red-contrib-modbus`** (Modbus client)
2. **`node-red-dashboard`** (Dashboard UI)

Aguarde a instalação. Atualize a página após terminar.

---

## 5. Procedimento

### Etapa 1 — Fluxo Básico: Conectar e Ler

Vamos começar simples: ler um registrador e exibir no debug.

**5.1.1** Arraste do palette para o canvas:
- 1 **inject** (timestamp)
- 1 **Modbus Read** (do grupo Modbus)
- 1 **debug**

Conecte: `inject → Modbus Read → debug`.

**5.1.2** Configure o **inject**:
- Double-click no node.
- **Repeat**: a cada `2 segundos`.
- Deixe `msg.payload` como timestamp default.

**5.1.3** Configure o **Modbus Read**:
- Double-click no node.
- **Name**: `Read EM3P measurements`
- **FC**: `FC 4: Read Input Registers`
- **Address**: `0`
- **Quantity**: `92` *(lê todas as medições de uma vez — boa prática!)*
- **Poll Rate**: deixe em `0` (vamos disparar pelo inject)
- **Server**: clique no lápis para criar um novo:
  - **Name**: `EM3P-1`
  - **Type**: `TCP`
  - **Host**: IP do smartphone (ex.: `192.168.0.105`)
  - **Port**: `5020`
  - **Unit ID**: `1`
  - **Reconnect on timeout**: ✓ habilitado
  - Add.
- Done.

**5.1.4** Clique em **Deploy** (botão vermelho no canto superior direito).

**5.1.5** No painel à direita, clique no ícone do **debug** (bug). Você deve ver mensagens chegando com `payload` = array de 92 inteiros.

> ✓ **Sucesso parcial:** se você vê a array de 92 inteiros, sua conexão Modbus TCP está funcionando.

---

### Etapa 2 — Decodificar FLOAT32

Adicione um node **function** entre o **Modbus Read** e o **debug**.

Double-click no function node:

```javascript
// Decodifica os principais valores do MK-EM3P
const regs = msg.payload;

function wordsToFloat(high, low) {
    const buffer = Buffer.alloc(4);
    buffer.writeUInt16BE(high, 0);
    buffer.writeUInt16BE(low, 2);
    return buffer.readFloatBE(0);
}

function wordsToUint32(high, low) {
    return (high << 16) | low;
}

const data = {
    timestamp: new Date().toISOString(),
    v_l1: wordsToFloat(regs[0], regs[1]),
    v_l2: wordsToFloat(regs[2], regs[3]),
    v_l3: wordsToFloat(regs[4], regs[5]),
    i_l1: wordsToFloat(regs[12], regs[13]),
    i_l2: wordsToFloat(regs[14], regs[15]),
    i_l3: wordsToFloat(regs[16], regs[17]),
    p_total: wordsToFloat(regs[26], regs[27]),
    pf_total: wordsToFloat(regs[50], regs[51]),
    frequency: wordsToFloat(regs[52], regs[53]),
    energy: wordsToUint32(regs[54], regs[55]),
    alarm_status: regs[90],
};

// Cálculos derivados
data.v_avg = (data.v_l1 + data.v_l2 + data.v_l3) / 3;
data.i_avg = (data.i_l1 + data.i_l2 + data.i_l3) / 3;
data.alarm_over_voltage = !!(data.alarm_status & 0x0001);
data.alarm_under_voltage = !!(data.alarm_status & 0x0002);
data.alarm_over_current = !!(data.alarm_status & 0x0004);

msg.payload = data;
return msg;
```

**Deploy.** No debug, você verá agora um objeto JSON com todos os valores decodificados.

---

### Etapa 3 — Dashboard Básico

Vamos criar gauges visuais.

**5.3.1** Adicione 3 nodes **gauge** (do grupo Dashboard). Conecte cada um a uma cópia da saída do function (você pode usar **link out** e **link in** para evitar fios visualmente).

Mais simples: adicione um node **change** que copia `msg.payload.v_l1` para `msg.payload`:
- Set `msg.payload` to `msg.payload.v_l1` (tipo: msg).

Conecte: `function → change → gauge L1`.

**5.3.2** Configure o primeiro gauge:
- **Group**: clique no lápis para criar um novo:
  - **Name**: `Tensões`
  - **Tab**: novo → **Name**: `EM3P Dashboard`
  - Add.
- **Type**: Gauge
- **Label**: `Voltage L1-N`
- **Units**: `V`
- **Range**: `200` a `260`
- **Sectors**: 200, 210, 250, 260 (verde no meio, vermelho nas extremidades)
- Done.

**5.3.3** Replique para L2 e L3 (mesmo grupo "Tensões").

**5.3.4** Crie um novo grupo "Correntes" e gauges para I_L1, I_L2, I_L3.

**5.3.5** Crie um novo grupo "Potência" e gauges para P_total, PF_total, Frequency.

**5.3.6** Deploy. Abra `http://localhost:1880/ui` em outra aba. Você verá o dashboard ao vivo!

---

### Etapa 4 — Gráfico Histórico

Adicione um node **chart** (Dashboard):

- **Group**: crie um novo "Histórico"
- **Type**: `Line chart`
- **Label**: `Tensões ao longo do tempo`
- **X-axis**: `last 5 minutes`
- **Y-axis**: min 200, max 260
- Done.

Conecte 3 cópias do function → 3 nodes **change** que extraem `msg.payload.v_l1`, `v_l2`, `v_l3` e ajustam `msg.topic` para `"L1"`, `"L2"`, `"L3"` (o chart usa o topic como nome da série).

Exemplo de change para L1:
- Set `msg.payload` to `msg.payload.v_l1`
- Set `msg.topic` to the string `"L1"`

Conecte os 3 changes ao mesmo chart.

**Deploy.** O gráfico mostra as 3 tensões ao longo do tempo.

---

### Etapa 5 — Painel de Alarmes

Adicione um node **text** (Dashboard) — exibe texto.

Antes dele, adicione um function que monta a mensagem de alarme:

```javascript
const d = msg.payload;
let alarms = [];
if (d.alarm_over_voltage)  alarms.push("⚠️ SOBRE-TENSÃO");
if (d.alarm_under_voltage) alarms.push("⚠️ SUB-TENSÃO");
if (d.alarm_over_current)  alarms.push("⚠️ SOBRE-CORRENTE");

msg.payload = alarms.length > 0 ? alarms.join(" | ") : "✓ OK";
msg.color = alarms.length > 0 ? "red" : "green";
return msg;
```

Configure o text node:
- **Group**: "Alarmes" (novo)
- **Label**: `Status:`
- **Layout**: `label value`

Para colorir conforme o status, use **ui_template** em vez de text — ele permite HTML/CSS:

```html
<div style="color: {{msg.color}}; font-weight: bold; font-size: 1.2em">
    {{msg.payload}}
</div>
```

---

### Etapa 6 — Logging em CSV

Adicione um node **file** (do grupo "storage"):

- **Filename**: `em3p_log.csv`
- **Action**: `append to file`
- **Add newline to each payload**: ✓

Antes do file, adicione um function que formata como linha CSV:

```javascript
const d = msg.payload;
const line = `${d.timestamp},${d.v_l1.toFixed(2)},${d.v_l2.toFixed(2)},${d.v_l3.toFixed(2)},${d.i_l1.toFixed(2)},${d.i_l2.toFixed(2)},${d.i_l3.toFixed(2)},${d.p_total.toFixed(2)},${d.pf_total.toFixed(3)},${d.frequency.toFixed(2)},${d.alarm_status}`;

msg.payload = line;
return msg;
```

**Para criar o header**, adicione um node **inject** com:
- **Payload**: string `"timestamp,v_l1,v_l2,v_l3,i_l1,i_l2,i_l3,p_total,pf_total,frequency,alarm_status"`
- **Inject once after start**: ✓
- Conecte a um node **file** separado (criar arquivo do zero):
  - **Filename**: `em3p_log.csv`
  - **Action**: `overwrite file`
  - **Add newline**: ✓

**Deploy.** Após alguns minutos, abra o arquivo `em3p_log.csv` na sua pasta do Node-RED (`~/.node-red/`) para conferir.

---

### Etapa 7 — Escrita de Configuração via Dashboard

Vamos permitir que o usuário altere o **Over-Voltage Threshold** pelo dashboard.

**5.7.1** Adicione um node **numeric** (Dashboard):
- **Group**: "Configuração"
- **Label**: `Over-Voltage Threshold`
- **Min**: `210`, **Max**: `270`
- **Step**: `0.5`
- **Default**: `253`

**5.7.2** Adicione um function que prepara os 2 registradores:

```javascript
const value = parseFloat(msg.payload);
const buffer = Buffer.alloc(4);
buffer.writeFloatBE(value, 0);
const high = buffer.readUInt16BE(0);
const low = buffer.readUInt16BE(2);

msg.payload = [high, low];
return msg;
```

**5.7.3** Adicione um node **Modbus Write**:
- **Name**: `Write OV Threshold`
- **FC**: `FC 16: Preset Multiple Registers`
- **Address**: `107`
- **Quantity**: `2`
- **Server**: use o mesmo "EM3P-1" criado antes.

**Deploy.** No dashboard, ajuste o slider e veja que ele escreve no equipamento.

**Verifique** lendo de volta com a leitura periódica que você já tem, ou pelo EasyModbusTCP em paralelo.

---

### Etapa 8 — Refinamentos (opcionais mas recomendados)

- **Status badges** para o estado de conexão (verde / vermelho).
- **Botão "Reset"** para zerar contadores de energia (escrever 0 no comando reset).
- **Gauges com setores coloridos** para indicar faixas saudáveis.
- **Múltiplos gráficos**: um para tensão, outro para corrente, outro para potência.
- **Botão "Exportar"** que disponibiliza o CSV.

---

## 6. Critérios de Sucesso

Você completou esta prática se:

- ✅ Configurou um **fluxo Node-RED** que lê o MK-EM3P periodicamente (Etapa 1).
- ✅ Implementou a **decodificação FLOAT32** em JavaScript (Etapa 2).
- ✅ Criou um **dashboard com gauges** para tensões, correntes e potência (Etapa 3).
- ✅ Adicionou um **gráfico histórico** com as 3 tensões (Etapa 4).
- ✅ Implementou um **painel de alarmes** colorido (Etapa 5).
- ✅ Gerou um **arquivo CSV** com pelo menos 30 linhas de dados (Etapa 6).
- ✅ **Alterou um parâmetro de configuração** pelo dashboard e verificou a escrita (Etapa 7).

---

## 7. Discussão e Reflexão

1. **Comparação.** Compare Node-RED com:
   - EasyModbusTCP (Prática 1)
   - Script Python (Prática 2)
   Em quais cenários cada um se sai melhor? Liste 3 vantagens e 3 desvantagens de cada.
2. **Arquitetura.** O Node-RED roda no seu laptop. Como você expandiria isso para que **vários usuários** acessem o dashboard simultaneamente?
3. **Persistência.** O CSV é adequado para até quantas amostras antes de virar problemático? Que alternativa você usaria para volumes maiores (10.000+ amostras)?
4. **Segurança.** Por padrão, o dashboard Node-RED está aberto a qualquer um na rede. Como você adicionaria autenticação?
5. **Confiabilidade.** Se o IP do smartphone mudar, o que acontece com seu fluxo? Como mitigar?

---

## 8. Entregáveis para Avaliação

Submeta:

1. **Captura(s) de tela** do dashboard funcionando, mostrando:
   - Todos os gauges com valores
   - Gráfico histórico com 3 séries
   - Painel de alarmes
   - Slider de configuração
2. **Export do fluxo** (menu ≡ → Export → All flows → JSON). Inclua esse JSON no relatório.
3. **Arquivo `em3p_log.csv`** com pelo menos 30 linhas.
4. **Análise dos dados do CSV**: gere um gráfico Excel/matplotlib mostrando a evolução de uma variável.
5. **Respostas** às 5 perguntas da seção 7.

---

## 9. Solução de Problemas Específicos

| Sintoma | Causa | Solução |
|---------|-------|---------|
| Node-RED não inicia | Node.js não instalado | Instale Node.js 18+ |
| Dashboard não aparece | Módulo não instalado | Manage palette → install `node-red-dashboard` |
| Modbus node não aparece | Módulo não instalado | Manage palette → install `node-red-contrib-modbus` |
| "Connection refused" no Modbus | App não em RUNNING ou porta errada | Confirme porta 5020 e START no app |
| Gauges não atualizam | Inject não está repetindo | Verifique "Repeat: every X seconds" no inject |
| FLOAT32 vem como NaN | Endereço errado ou ordem trocada | Confirme registradores e ABCD |
| CSV não está sendo criado | Permissão de pasta | Veja `~/.node-red/` ou pasta atual |

---

## 10. Próximos Passos

- **[Prática 6 — VFD7 com Node-RED](16-pratica-vfd7-nodered.md)**: amplie para controle de inversor.
- **[Práticas em Grupo (1 a 4)](10-praticas-visao-geral.md#práticas-em-grupo)**: coordene múltiplos dispositivos com colegas.

---

**Excelente trabalho!**
