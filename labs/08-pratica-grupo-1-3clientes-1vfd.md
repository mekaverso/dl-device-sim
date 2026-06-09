# Prática Grupo 1 — 3 Clientes Operando 1 VFD

> *"Em qualquer planta industrial, um único equipamento é tipicamente observado por múltiplos sistemas — mas comandado por apenas um. Vamos viver isso na prática."*

## 1. Contexto Industrial

Em uma planta real, um único inversor de frequência é tipicamente acessado simultaneamente por:

- **O HMI local** (painel na máquina, controle do operador)
- **O sistema SCADA central** (visualização do supervisor)
- **A estação de engenharia/manutenção** (diagnóstico)
- **Servidores de histórico** (data logging)

Todos **leem** os mesmos dados, mas somente **um cliente** detém a **autoridade de escrita** em um dado momento. Isso é uma **convenção organizacional** — Modbus TCP em si não impõe essa restrição. Em SCADAs industriais profissionais, isso é gerenciado via "tokens de comando", "lock de operação" ou simplesmente regras operacionais documentadas.

Nesta prática, vocês vão experimentar essa arquitetura na prática: **3 clientes acessando 1 VFD**, cada um com um **papel distinto e dashboards adequados ao papel**.

---

## 2. Papéis na Equipe

A equipe de **3 alunos** assume os seguintes papéis:

| Aluno | Papel | Acesso ao VFD | Foco do Dashboard |
|-------|-------|---------------|-------------------|
| **A** | **Operador**            | Read + **Write** | Controle (start/stop, setpoint) + monitoração |
| **B** | **Supervisor de sala**  | Read-only        | Visão geral, gráficos, KPIs |
| **C** | **Engenharia/Manutenção** | Read-only      | Diagnóstico (corrente, temperatura, falhas, histórico de eventos) |

> Os três acessam o **mesmo VFD** simultaneamente, mas apenas o **Operador A** comanda. **B e C** observam.

> **Rotação:** após executar as etapas, a equipe **rotaciona os papéis** (A → B → C → A), de forma que todos experimentem os três pontos de vista.

---

## 3. Material Necessário

- **1 smartphone Android** com **ModbusDeviceSIM** instalado (qualquer aluno fornece — chamamos de "smartphone do VFD")
- **3 laptops** (um por aluno), com:
  - **Node-RED** instalado
  - Pacotes `node-red-contrib-modbus` e `node-red-dashboard`
- **Rede Wi-Fi** comum a todos os 4 dispositivos

---

## 4. Setup

### 4.1 Dispositivo VFD (smartphone)

1. Abra o **ModbusDeviceSIM**.
2. Selecione **MK-VFD7**.
3. Toque em **START**.
4. **Coloque em modo REMOTE** (switch no painel do app).
5. Anote o IP exibido — exemplo: `192.168.1.50:5020`.
6. Mantenha a tela acesa durante toda a prática.

### 4.2 Verificação de Conectividade

**Cada aluno** abre o terminal no seu laptop e executa:

```
ping 192.168.1.50
```

Os 3 pings devem responder. **Não prossigam até resolver** se algum laptop não conseguir alcançar o smartphone.

---

## 5. Conceitos Necessários (Resumo)

### 5.1 Mapa de Registradores do MK-VFD7

| Endereço | Variável             | Tipo    | Acesso |
|----------|----------------------|---------|--------|
| 0–1      | Output Frequency     | FLOAT32 | R      |
| 4–5      | Output Current       | FLOAT32 | R      |
| 8–9      | Motor Speed          | FLOAT32 | R      |
| 14–15    | Drive Temperature    | FLOAT32 | R      |
| 18–19    | Run Time (horas)     | UINT32  | R      |
| 26       | Drive Status (bits)  | UINT16  | R      |
| 27       | Fault Code           | UINT16  | R      |
| 100      | Control Word         | UINT16  | R/W    |
| 101–102  | Frequency Reference  | FLOAT32 | R/W    |

### 5.2 Control Word Valores

| Valor | Ação         |
|-------|--------------|
| 0     | Stop         |
| 1     | Run forward  |
| 3     | Run reverse  |
| 8     | Fault Reset  |

### 5.3 Decodificação FLOAT32 em JavaScript (Node-RED)

```javascript
function wordsToFloat(h, l) {
    const buf = Buffer.alloc(4);
    buf.writeUInt16BE(h, 0);
    buf.writeUInt16BE(l, 2);
    return buf.readFloatBE(0);
}
```

---

## 6. Procedimento

> **Todos os 3 alunos** trabalham **em paralelo** nas Etapas 1 a 4, cada um implementando seu dashboard específico. As Etapas 5 e 6 são executadas conjuntamente.

### Etapa 1 — Conexão e Verificação Multi-cliente (15 min)

**Os 3 alunos simultaneamente:**

1. Abram Node-RED (`http://localhost:1880`).
2. Configurem um servidor Modbus comum (cada um no seu Node-RED):
   - Nome: `VFD-Compartilhado`
   - Host: IP do smartphone
   - Porta: `5020`
   - Unit ID: `1`
3. Criem um fluxo mínimo: `inject (1s) → Modbus Read FC04, addr 0, qty 29 → debug`.
4. Deploy.

**Verifiquem no smartphone:** o contador **Clients** sobe para **3** — uma conexão por aluno. ✓

> **Se o contador mostra menos de 3:** algum aluno não conectou. Investiguem antes de seguir.

---

### Etapa 2 — Aluno A: Dashboard do Operador (45 min)

O dashboard do operador **inclui controles** (botões e slider). Implemente:

#### 2.1 Decodificação e leitura periódica

Após o `Modbus Read`, adicione um **function** para decodificar o estado:

```javascript
const regs = msg.payload;
function f32(h, l) {
    const b = Buffer.alloc(4);
    b.writeUInt16BE(h, 0);
    b.writeUInt16BE(l, 2);
    return b.readFloatBE(0);
}
const s = regs[26];
msg.payload = {
    frequency: f32(regs[0], regs[1]),
    current:   f32(regs[4], regs[5]),
    speed:     f32(regs[8], regs[9]),
    running:        !!(s & 0x0001),
    forward:        !!(s & 0x0002),
    reverse:        !!(s & 0x0004),
    at_reference:   !!(s & 0x0008),
    accelerating:   !!(s & 0x0010),
    decelerating:   !!(s & 0x0020),
    fault:          !!(s & 0x0040),
    fault_code:     regs[27],
    warning_code:   regs[28],
};
return msg;
```

#### 2.2 Widgets de controle

- **Gauge**: Output Frequency (0–60 Hz)
- **Gauge**: Output Current (0–25 A)
- **LEDs virtuais**: RUN, FWD, REV, REF, FAULT (use ui_template)
- **Botões**:
  - `▶ START FWD` → escreve `1` no reg 100 (FC06)
  - `◄ START REV` → escreve `3` no reg 100 (FC06)
  - `■ STOP` → escreve `0` no reg 100 (FC06)
  - `⟲ FAULT RESET` → escreve `8`, depois `0` (com 200ms entre eles)
- **Slider**: Frequency Reference (0–60 Hz), escreve FC16 no reg 101–102 (FLOAT32)

#### 2.3 Indicador de papel

Adicione um **ui_template** no topo:

```html
<div style="background:#1f5a1f; color:#fff; padding:8px; border-radius:6px; text-align:center">
    <h3>OPERADOR (Aluno A) — Controle ativo deste VFD</h3>
</div>
```

> Deploy. O dashboard do operador está pronto. Aluno A não toca em nada ainda.

---

### Etapa 3 — Aluno B: Dashboard do Supervisor (45 min)

O supervisor **observa toda a operação**, foca em **tendências e KPIs**. **Sem botões de comando.**

#### 3.1 Widgets

- **Gauge grande**: Output Frequency (0–60 Hz)
- **Gauge grande**: Motor Speed (0–1800 RPM)
- **Gauge**: Output Current (0–25 A)
- **Chart histórico** (5 min): Frequency
- **Chart histórico** (5 min): Current
- **KPI text**: Run Time (decodificar UINT32 dos registradores 18–19)
- **KPI text**: "Eficiência estimada" — calcule como `(motor_speed / 1800) * 100` (%)
- **Indicador de status global**: ui_template colorido conforme `running`/`fault`

#### 3.2 Decodificação adicional para Run Time

Adicione no function (após decodificação principal):

```javascript
// Após Modbus Read, decodifique também UINT32
msg.payload.run_time_hours = (regs[18] << 16) | regs[19];
```

#### 3.3 Indicador de papel

```html
<div style="background:#1a3250; color:#fff; padding:8px; border-radius:6px; text-align:center">
    <h3>SUPERVISOR (Aluno B) — Apenas observação</h3>
</div>
```

#### 3.4 KPI calculado: tempo desde último start

Em um function, mantenha estado para detectar quando `running` mudou de `false` para `true`:

```javascript
const now = Date.now();
const wasRunning = context.get("wasRunning") || false;
const startTime  = context.get("startTime") || null;

if (msg.payload.running && !wasRunning) {
    // transição: parou → rodando
    context.set("startTime", now);
}
context.set("wasRunning", msg.payload.running);

const sinceStart = msg.payload.running && startTime
    ? Math.round((now - startTime) / 1000)
    : 0;

msg.payload.seconds_since_start = sinceStart;
return msg;
```

Exiba esse valor em um **ui_text** ou **ui_template**.

> Aluno B agora tem um dashboard "supervisor" com tendências e KPIs.

---

### Etapa 4 — Aluno C: Dashboard de Engenharia/Manutenção (45 min)

A perspectiva de manutenção foca em **diagnóstico** e **detalhes de longo prazo**.

#### 4.1 Widgets

- **Gauge**: Drive Temperature (20–100 °C) — com setores: 20–70 verde, 70–85 amarelo, 85+ vermelho
- **Gauge**: Output Current (0–25 A) — com setores conforme limites
- **Display destacado**: Fault Code (UINT16) e Warning Code (UINT16) — em fonte grande
- **Painel de status detalhado** (ui_template): expanda o Status Word bit a bit com tabela colorida
- **Chart histórico** (15 min): Drive Temperature
- **Chart histórico** (15 min): Current
- **Lista de eventos**: cada transição de estado importante (start, stop, fault, fault reset) gera uma linha de log

#### 4.2 Painel de status detalhado

ui_template:

```html
<table style="width:100%; color:#ddd; font-family:monospace; font-size:0.9em">
  <tr><td>Bit 0 — RUNNING</td><td>{{msg.payload.running ? '✓ ATIVO' : '· inativo'}}</td></tr>
  <tr><td>Bit 1 — FORWARD</td><td>{{msg.payload.forward ? '✓ ATIVO' : '· inativo'}}</td></tr>
  <tr><td>Bit 2 — REVERSE</td><td>{{msg.payload.reverse ? '✓ ATIVO' : '· inativo'}}</td></tr>
  <tr><td>Bit 3 — AT REFERENCE</td><td>{{msg.payload.at_reference ? '✓ ATIVO' : '· inativo'}}</td></tr>
  <tr><td>Bit 4 — ACCELERATING</td><td>{{msg.payload.accelerating ? '✓ ATIVO' : '· inativo'}}</td></tr>
  <tr><td>Bit 5 — DECELERATING</td><td>{{msg.payload.decelerating ? '✓ ATIVO' : '· inativo'}}</td></tr>
  <tr><td>Bit 6 — FAULT</td><td><span ng-style="{color: msg.payload.fault ? '#ff6868' : '#888'}">{{msg.payload.fault ? '⚠ FALHA' : '✓ OK'}}</span></td></tr>
</table>
```

#### 4.3 Lista de eventos (event log)

Em um function, detecte transições e mantenha uma lista:

```javascript
const events = flow.get("events") || [];
const prev   = flow.get("prev") || {};
const cur    = msg.payload;
const ts     = new Date().toISOString().substring(11, 19);

function pushEvent(text) {
    events.push(`[${ts}] ${text}`);
    if (events.length > 50) events.shift();
}

if (cur.running && !prev.running)             pushEvent("✓ START");
if (!cur.running && prev.running)             pushEvent("■ STOP");
if (cur.fault && !prev.fault)                  pushEvent(`⚠ FAULT (code ${cur.fault_code})`);
if (!cur.fault && prev.fault)                  pushEvent("✓ Fault cleared");
if (cur.reverse && !prev.reverse)             pushEvent("◄ Reverse direction");

flow.set("events", events);
flow.set("prev", cur);

msg.payload = events.join("\n");
return msg;
```

Exiba em um **ui_text** com formato multilinha (ou ui_template `<pre>`).

#### 4.4 Indicador de papel

```html
<div style="background:#5a3a1f; color:#fff; padding:8px; border-radius:6px; text-align:center">
    <h3>ENGENHARIA / MANUTENÇÃO (Aluno C) — Diagnóstico</h3>
</div>
```

> Aluno C tem agora um dashboard de manutenção com diagnósticos profundos.

---

### Etapa 5 — Operação Coordenada (30 min)

Agora os 3 dashboards estão prontos e conectados ao mesmo VFD. Posicione os 3 laptops lado a lado.

**Sequência conduzida pelo Aluno A (Operador):**

1. Aluno A define **Frequência = 25 Hz** no slider.
2. Aluno A pressiona **▶ START FWD**.
   - Aluno B observa no chart o crescimento da frequência e do current.
   - Aluno C observa o aumento de temperatura, os bits ACC e RUN ativos, e a entrada de evento no log.
3. Aluno A aguarda o LED REF acender (frequência estabilizada).
4. Aluno A muda a frequência para **50 Hz**.
   - Aluno B observa a nova rampa nos gráficos.
   - Aluno C observa pico de current, ACC ativo, e o KPI "seconds_since_start" continuando a contar.
5. Aluno A pressiona **◄ START REV** (mudança de direção em pleno funcionamento).
   - Os 3 observam a desaceleração até zero e nova aceleração em reverso.
   - Aluno C vê o evento "Reverse direction" no log.
6. Aluno A pressiona **■ STOP**.
   - Todos observam a desaceleração.
7. (Opcional) **Provoque uma falha**: temporariamente reduza Over-Current Threshold (reg 119–120, FLOAT32 ABCD) para abaixo do current atual via outro cliente (ex.: EasyModbusTCP aberto pelo Aluno A).
   - Drive entra em fault.
   - Aluno C vê fault_code aparecer, LED FLT aceso, evento no log.
   - Aluno A executa **⟲ FAULT RESET**.
   - Aluno C confirma "Fault cleared" no log.

---

### Etapa 6 — Rotação de Papéis (45 min)

Repitam toda a Etapa 5, mas agora **rotacionando**:

- **Operador**: B → quem antes era Supervisor
- **Supervisor**: C → quem antes era Engenharia
- **Engenharia**: A → quem antes era Operador

> A pessoa que **agora vira Operador** terá que **adaptar seu fluxo** Node-RED para incluir controles, ou apenas usar o do Aluno A previamente — combine na equipe.

**Mais prática:** rotacione **uma vez mais**, completando o ciclo (cada aluno passa por todos os papéis).

---

### Etapa 7 — Análise Coletiva (15 min)

Os 3 alunos comparam:

1. **Defasagem temporal**: quando o Operador comandou START, em quanto tempo o Supervisor e o Engenharia viram a mudança? Use os timestamps dos charts.
2. **Consistência**: os valores exibidos nos 3 dashboards são iguais? Tirem screenshots simultâneos para comparar.
3. **Carga no servidor**: o smartphone sustentou 3 clientes simultâneos sem problemas? Houve algum erro de comunicação durante a sessão?

---

## 7. Critérios de Sucesso

A equipe completou esta prática se:

- ✅ Os 3 dashboards estão funcionando em paralelo, conectados ao mesmo VFD.
- ✅ O smartphone mostra **3 clientes** conectados durante a operação.
- ✅ O dashboard do **Operador** controla efetivamente o VFD (start, stop, freq, reverse, fault reset).
- ✅ O dashboard do **Supervisor** mostra gráficos históricos e KPIs calculados.
- ✅ O dashboard de **Engenharia** mostra a tabela bit-a-bit do status e o log de eventos.
- ✅ A equipe executou a **rotação completa de papéis** (cada aluno passou pelos 3).

---

## 8. Discussão e Reflexão

A equipe responde coletivamente:

1. **Concorrência de leitura.** Vocês confirmaram que 3 clientes podem ler simultaneamente sem problemas. Em uma planta com 50 sistemas lendo o mesmo CLP, o que poderia dar errado? Pesquisem o conceito de **"connection pool"** e como CLPs profissionais lidam com isso.
2. **Autoridade de escrita.** Modbus TCP **não impede** que o Supervisor (que tem só read-only por convenção) envie um comando de escrita. Como organizações industriais asseguram que **apenas o operador autorizado** comande? Pesquisem **role-based access control** em SCADA.
3. **Defasagem.** Compararam a defasagem temporal entre os 3 dashboards. Em uma operação crítica (ex.: alarme de segurança), quanto atraso é aceitável? Quanto seu sistema entrega?
4. **Arquitetura.** Esta arquitetura (todos os clientes acessam diretamente o dispositivo) escala? Para 100 estações de operação, vocês manteriam essa topologia ou mudariam para um **gateway/proxy intermediário**? Justifiquem.
5. **Reflexão.** Em qual papel **vocês se sentiram mais confortáveis**? O que esse papel ensina sobre o que **a engenharia industrial valoriza**? (foco em controle, em tendências, em diagnóstico).

---

## 9. Entregáveis (equipe)

Um único relatório de equipe contendo:

1. **Tabela** com IPs e papéis ao longo da rotação.
2. **Screenshots simultâneos** dos 3 dashboards em pelo menos 3 momentos da operação:
   - Drive parado
   - Drive acelerando
   - Drive em referência
3. **Captura do smartphone** mostrando 3 clientes conectados.
4. **Export dos 3 fluxos Node-RED** (JSON).
5. **Análise de defasagem temporal**: extraia os dados dos charts e calcule, para um evento específico (ex.: o START), em quantos ms cada dashboard recebeu a notícia.
6. **Vídeo curto (2-3 min)** mostrando a operação coordenada com os 3 laptops lado a lado.
7. **Respostas** às 5 perguntas da seção 8.

---

## 10. Solução de Problemas Específicos

| Sintoma | Causa | Solução |
|---------|-------|---------|
| Smartphone trava com 3 clientes | Memória/CPU baixa do Android | Feche outros apps; mantenha a tela acesa |
| Apenas 2 conexões mostradas | Algum laptop não conectou | Verifique IPs, firewall, ping |
| Aluno B/C envia comando "por engano" | Convenção quebrada | Reforce que só o Operador comanda — não há proteção técnica |
| Dashboards mostram valores divergentes | Timing diferente de polling | Aceito — pequena defasagem é normal |
| Slider do Operador "salta" para valores antigos | Polling sobrescreve estado da UI | Configure dashboard para não sobrescrever input ativo |

---

## 11. Próximas Práticas em Grupo

- **[Prática Grupo 2 — 1 cliente, 3 VFDs](09-pratica-grupo-2-1cliente-3vfds.md)**: orquestração centralizada.
- **[Prática Grupo 3 — 3 clientes, 3 VFDs](10-pratica-grupo-3-3clientes-3vfds.md)**: operação distribuída independente.
- **[Prática Grupo 4 — Mini-planta integrada](11-pratica-grupo-4-mini-planta.md)**: 2 VFDs + 1 medidor com papéis distintos.

---

**Boa equipe!**

— **Prof. Dênis Leite**
*Mekatronik — Advanced Engineering*
