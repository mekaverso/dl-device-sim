# Prática 6 — MK-VFD7 com Node-RED

> *"Construa em 30 minutos a IHM que faria sentido numa máquina real."*

## 1. Contexto Industrial

Em plantas industriais, **IHMs** (interfaces homem-máquina) controlam inversores diariamente. Tipicamente são telas dedicadas (Schneider Magelis, Siemens KTP, etc.) ou software supervisório (FactoryTalk, WinCC). Mas para **aplicações menores** ou **prototipagem rápida**, ferramentas como **Node-RED** entregam soluções comparáveis em **uma fração do tempo e do custo**.

Uma IHM típica para inversor deve permitir:

- **Start/Stop** com confirmação visual
- **Forward/Reverse** com indicador de direção
- **Ajuste de velocidade** (slider ou input numérico)
- **Visualização em tempo real** de frequência, corrente, velocidade
- **Indicadores de estado** (LEDs virtuais)
- **Alarmes e fault display**
- **Histórico** das últimas operações

Nesta prática, você construirá essa IHM do zero usando Node-RED.

---

## 2. Conceitos Necessários

### 2.1 Conceitos Node-RED — referência rápida

- **Inject**: dispara fluxos periodicamente.
- **Modbus Read / Write**: comunica com o dispositivo.
- **Function**: lógica em JavaScript.
- **Change**: manipula `msg.payload`.
- **Switch**: roteia conforme condições.
- **UI** (dashboard): widgets para o usuário (gauge, button, slider, chart, text).

### 2.2 Mapa do MK-VFD7

Veja mapa completo na [Prática 4](14-pratica-vfd7-easymodbus.md). Resumo:

| Endereço | Variável             | Tipo    | Acesso |
|----------|----------------------|---------|--------|
| 0–1      | Output Frequency     | FLOAT32 | R      |
| 4–5      | Output Current       | FLOAT32 | R      |
| 8–9      | Motor Speed          | FLOAT32 | R      |
| 26       | Drive Status (bits)  | UINT16  | R      |
| 27       | Fault Code           | UINT16  | R      |
| 100      | Control Word (bits)  | UINT16  | R/W    |
| 101–102  | Frequency Reference  | FLOAT32 | R/W    |

### 2.3 Control Word valores

| Valor | Ação         |
|-------|--------------|
| 0     | Stop         |
| 1     | Run forward  |
| 3     | Run reverse  |

### 2.4 Decodificação FLOAT32 em JavaScript

```javascript
function wordsToFloat(high, low) {
    const buf = Buffer.alloc(4);
    buf.writeUInt16BE(high, 0);
    buf.writeUInt16BE(low, 2);
    return buf.readFloatBE(0);
}

function floatToWords(value) {
    const buf = Buffer.alloc(4);
    buf.writeFloatBE(value, 0);
    return [buf.readUInt16BE(0), buf.readUInt16BE(2)];
}
```

---

## 3. Material Necessário

- 1 **smartphone Android** com **ModbusDeviceSIM**, modo **REMOTE**
- 1 **laptop** com **Node.js 18+** e **Node-RED**
- Conexão Wi-Fi compartilhada
- Pacotes Node-RED: `node-red-contrib-modbus` e `node-red-dashboard`

---

## 4. Setup Inicial

### 4.1 No smartphone

1. Abra ModbusDeviceSIM, selecione **MK-VFD7**, **START**.
2. **Coloque em REMOTE** (switch no painel).
3. Anote IP.

### 4.2 No laptop

Se Node-RED ainda não estiver instalado (veja Prática 3 para passo-a-passo):

```bash
npm install -g --unsafe-perm node-red
node-red
```

Abra `http://localhost:1880`.

Instale via Manage Palette se ainda não tem:
- `node-red-contrib-modbus`
- `node-red-dashboard`

---

## 5. Procedimento

### Etapa 1 — Configurar o Servidor Modbus

Adicione um nó **Modbus Read** ao canvas e configure o servidor (uma vez para todo o fluxo):

- **Name**: `VFD7-1`
- **Type**: `TCP`
- **Host**: IP do smartphone
- **Port**: `5020`
- **Unit ID**: `1`
- **Reconnect on timeout**: ✓

Esse servidor será reutilizado por todos os Modbus nodes do fluxo.

---

### Etapa 2 — Leitura Periódica + Decodificação

**5.2.1** Adicione:
- 1 **inject** (repetir a cada 1 segundo)
- 1 **Modbus Read** configurado:
  - FC: `FC 4: Read Input Registers`
  - Address: `0`
  - Quantity: `29` *(cobre frequência, corrente, velocidade, status, fault, warning)*
  - Server: `VFD7-1`
- 1 **function** node de decodificação

Conecte: `inject → Modbus Read → function`.

**5.2.2** No function node, cole:

```javascript
const regs = msg.payload;

function wordsToFloat(h, l) {
    const buf = Buffer.alloc(4);
    buf.writeUInt16BE(h, 0);
    buf.writeUInt16BE(l, 2);
    return buf.readFloatBE(0);
}

const status = regs[26];

msg.payload = {
    timestamp: new Date().toISOString(),
    frequency: wordsToFloat(regs[0], regs[1]),
    voltage:   wordsToFloat(regs[2], regs[3]),
    current:   wordsToFloat(regs[4], regs[5]),
    power:     wordsToFloat(regs[6], regs[7]),
    speed:     wordsToFloat(regs[8], regs[9]),
    torque:    wordsToFloat(regs[10], regs[11]),
    drive_temp: wordsToFloat(regs[14], regs[15]),
    status_raw: status,
    running:       !!(status & 0x0001),
    forward:       !!(status & 0x0002),
    reverse:       !!(status & 0x0004),
    at_reference:  !!(status & 0x0008),
    accelerating:  !!(status & 0x0010),
    decelerating:  !!(status & 0x0020),
    fault:         !!(status & 0x0040),
    fault_code: regs[27],
    warning_code: regs[28],
};
return msg;
```

**Deploy**, conecte um **debug** ao final para confirmar que recebe o objeto.

---

### Etapa 3 — Gauges de Monitoração

Crie uma aba "VFD7 Dashboard" no menu Dashboard.

Adicione 4 gauges, cada um precedido por um **change** que extrai a variável.

**Gauge: Output Frequency**
- Change: set `msg.payload` to `msg.payload.frequency`
- Gauge: Group "Operação", Range 0–60 Hz, Unit `Hz`

**Gauge: Output Current**
- Change: `msg.payload.current`
- Gauge: Range 0–30 A, Unit `A`

**Gauge: Motor Speed**
- Change: `msg.payload.speed`
- Gauge: Range 0–1800 RPM, Unit `RPM`

**Gauge: Drive Temperature**
- Change: `msg.payload.drive_temp`
- Gauge: Range 20–100 °C, Unit `°C`
- Sectors: 20-70 verde, 70-85 amarelo, 85+ vermelho

Deploy. Veja em `http://localhost:1880/ui`.

---

### Etapa 4 — Indicadores de Status (LEDs Virtuais)

Use **ui_template** para criar LEDs estilizados.

Adicione um function que prepara o HTML:

```javascript
const d = msg.payload;
const leds = [
    { label: "RUN",  on: d.running,       color: "#4ade80" },
    { label: "FWD",  on: d.forward,       color: "#3d8bff" },
    { label: "REV",  on: d.reverse,       color: "#ef8e5e" },
    { label: "REF",  on: d.at_reference,  color: "#4ade80" },
    { label: "ACC",  on: d.accelerating,  color: "#efcb1d" },
    { label: "DEC",  on: d.decelerating,  color: "#efcb1d" },
    { label: "FLT",  on: d.fault,         color: "#ef4444" },
];
msg.leds = leds;
return msg;
```

ui_template (Group "Status"):

```html
<div style="display:flex; gap:10px; justify-content:space-around; padding:8px">
  <div ng-repeat="led in msg.leds" style="text-align:center">
    <div ng-style="{
        background: led.on ? led.color : '#333',
        boxShadow: led.on ? '0 0 8px ' + led.color : 'none',
        width:18, height:18, borderRadius:'50%', margin:'auto'
    }"></div>
    <div style="color:#ccc; font-size:0.7em; margin-top:4px">{{led.label}}</div>
  </div>
</div>
```

Deploy. Você verá uma fila de LEDs coloridos. Os que estão ativos brilham.

---

### Etapa 5 — Botões de Controle

#### Botão START Forward

Adicione um **ui_button** (Group "Controles"):
- **Label**: `▶ START FWD`
- **Background**: verde

Conecte a um **function**:
```javascript
msg.payload = 1;  // Control Word: bit 0 = RUN
return msg;
```

Conecte a um **Modbus Write**:
- FC: `FC 6: Preset Single Register`
- Address: `100`
- Server: `VFD7-1`

#### Botão STOP

Mais um **ui_button**:
- **Label**: `■ STOP`
- **Background**: vermelho

Function: `msg.payload = 0;`
→ Modbus Write reg 100.

#### Botão REVERSE

Mais um **ui_button**:
- **Label**: `◄ START REV`

Function: `msg.payload = 3;` *(bits 0+1 = RUN + REVERSE)*
→ Modbus Write reg 100.

#### Botão FAULT RESET

Mais um **ui_button**:
- **Label**: `⟲ FAULT RESET`

Function:
```javascript
// Pulso: 8 → 0
msg.payload = 8;
// Envia uma segunda mensagem após 200ms
setTimeout(() => {
    node.send({payload: 0});
}, 200);
return msg;
```
→ Modbus Write reg 100.

Deploy. Você agora tem os botões básicos no dashboard.

---

### Etapa 6 — Slider de Frequência

Adicione um **ui_slider** (Group "Controles"):
- **Label**: `Frequência (Hz)`
- **Range**: 0 a 60
- **Step**: 0.5

Conecte a um **function** que converte para os 2 registradores:

```javascript
const freq = parseFloat(msg.payload);
const buf = Buffer.alloc(4);
buf.writeFloatBE(freq, 0);
msg.payload = [buf.readUInt16BE(0), buf.readUInt16BE(2)];
return msg;
```

Conecte a um **Modbus Write**:
- FC: `FC 16: Preset Multiple Registers`
- Address: `101`
- Quantity: `2`

Deploy. Mova o slider — o setpoint deve mudar em tempo real.

---

### Etapa 7 — Gráfico Histórico

Adicione um **ui_chart** (Group "Histórico"):
- **Type**: Line chart
- **X-axis**: last 5 minutes
- **Y-axis**: 0 a 60
- **Label**: `Frequência ao longo do tempo`

Adicione um **change** antes:
- Set `msg.payload` to `msg.payload.frequency`
- Set `msg.topic` to `"Freq"`

Conecte da saída do function de decodificação ao change → chart.

Deploy. Comece a operar (start/stop/mudar frequência) e veja o gráfico se preencher.

---

### Etapa 8 — Painel de Falha

Adicione um **ui_template** (Group "Diagnóstico"):

```html
<div ng-if="msg.payload.fault" style="background:#5a1f1f; padding:10px; border-radius:8px; color:#fee">
    <h3 style="color:#ff6868">⚠ FALHA ATIVA</h3>
    <p>Fault code: <strong>{{msg.payload.fault_code}}</strong></p>
    <p>Pressione <em>FAULT RESET</em> para limpar.</p>
</div>
<div ng-if="!msg.payload.fault" style="background:#1f5a1f; padding:10px; border-radius:8px; color:#efe">
    <h3 style="color:#68ff68">✓ OPERAÇÃO NORMAL</h3>
</div>
```

Conecte da saída do function principal.

Deploy. O painel agora muda de cor conforme o estado.

---

### Etapa 9 — Logging em CSV

Adicione um **file** node (similar à Prática 3):

Function que formata linha:
```javascript
const d = msg.payload;
msg.payload = `${d.timestamp},${d.frequency.toFixed(2)},${d.current.toFixed(2)},${d.speed.toFixed(1)},${d.status_raw},${d.fault_code},${d.warning_code}`;
return msg;
```

file:
- **Filename**: `vfd7_log.csv`
- **Action**: append
- **Add newline**: ✓

E um inject "once on start" criando o header:
- Payload string: `"timestamp,frequency,current,speed,status,fault,warning"`
- File (separado): overwrite mode, mesmo arquivo.

Deploy.

---

### Etapa 10 — Toques Finais

Refinamentos sugeridos:

- **Confirmação** antes de STOP em situações críticas (use `ui_alert`)
- **Indicador de conexão** (verde = OK, vermelho = perdeu conexão com o drive)
- **Botão Jog Forward**: Control Word = 5 enquanto pressionado, 0 ao soltar
- **Limites de slider**: bloquear setpoint acima de uma frequência máxima configurada

---

## 6. Critérios de Sucesso

Você completou esta prática se:

- ✅ Configurou conexão Modbus TCP estável (Etapa 1).
- ✅ Decodificou status, frequência, corrente, velocidade corretamente (Etapa 2).
- ✅ Dashboard com **gauges funcionando** (Etapa 3).
- ✅ **LEDs virtuais** refletem o estado real (Etapa 4).
- ✅ **Botões Start/Stop/Reverse/Fault Reset** funcionam (Etapa 5).
- ✅ **Slider** de frequência altera a referência em tempo real (Etapa 6).
- ✅ **Gráfico histórico** mostra a frequência ao longo do tempo (Etapa 7).
- ✅ **Painel de falha** muda de cor conforme estado (Etapa 8).
- ✅ Gerou arquivo CSV com pelo menos 60 amostras (Etapa 9).

---

## 7. Discussão e Reflexão

1. **Arquitetura.** Compare seu fluxo Node-RED com:
   - O script Python da Prática 5
   - O EasyModbusTCP da Prática 4
   Em quais aspectos cada um se sai melhor?
2. **Usabilidade.** Em uma planta real, um operador usaria sua IHM em situações de emergência. Que melhorias você proporia para garantir confiabilidade? Pense em:
   - Confirmação de comandos críticos
   - Indicação clara de estado
   - Tolerância a falhas de rede
3. **Segurança.** Atualmente seu dashboard está acessível a qualquer um na rede via `http://localhost:1880/ui`. Como você adicionaria autenticação?
4. **Escalabilidade.** Como você adaptaria esse fluxo para controlar **5 inversores** simultaneamente?
5. **Reflexão.** Para a maioria dos casos de uso reais, Node-RED é "rápido demais" ou "lento demais"? Discuta a latência de comunicação Modbus-TCP percebida no dashboard.

---

## 8. Entregáveis para Avaliação

Submeta:

1. **Capturas de tela** do dashboard mostrando:
   - Drive parado (todos os LEDs apagados exceto pré-condições)
   - Drive acelerando (LED ACC + frequência crescendo)
   - Drive em referência (LED REF aceso, gauge estabilizado)
   - Drive em reverse
   - Painel de falha ativo (após Etapa 8 e provocar falha, se possível)
2. **Export do fluxo** completo (Menu → Export → All flows → JSON).
3. **Arquivo CSV** com pelo menos 60 amostras incluindo eventos de start/stop/direção.
4. **Vídeo curto** (até 2 minutos) mostrando a operação do dashboard. Pode ser screencast.
5. **Respostas** às 5 perguntas da seção 7.

---

## 9. Solução de Problemas Específicos

| Sintoma | Causa | Solução |
|---------|-------|---------|
| Botões não enviam comandos | Modbus Write não configurado | Verifique FC, address, server |
| Drive não responde aos comandos | App em LOCAL | Mude para REMOTE |
| LEDs ficam todos apagados | Drive não está rodando ou status = 0 | Pressione START |
| Slider escreve mas drive não acelera | Não comandou RUN | Pressione START após mover slider |
| Gauge oscila demais | Polling muito rápido | Aumente o inject para 1-2s |
| File node não cria CSV | Permissão de pasta | Verifique pasta atual do Node-RED |

---

## 10. Próximos Passos

- **[Prática 7 — Multi-dispositivos em grupo](17-pratica-grupo-multi-dispositivos.md)**: a culminação — integre múltiplos dispositivos com 3 colegas.

---

**Sua primeira IHM industrial está pronta!**
