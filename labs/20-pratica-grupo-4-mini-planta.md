# Prática Grupo 4 — Mini-planta Integrada (2 VFDs + 1 Medidor)

> *"A culminação. Três operadores, três sistemas, papéis bem distintos, uma planta funcionando."*

## 1. Contexto Industrial

Imagine uma **mini-estação de bombeamento** de uma indústria química ou de tratamento de água. A planta consiste em:

- **2 bombas trifásicas** acionadas por inversores de frequência — controlam vazão.
- **1 medidor de energia** no quadro geral — monitora consumo total, qualidade da energia, alarmes elétricos.
- **3 operadores humanos** com responsabilidades distintas:
  - **Operador de Energia** — monitora o medidor, autoriza partidas, identifica problemas elétricos.
  - **Operador de Bomba 1** — comanda a Bomba 1 dentro das autorizações.
  - **Operador de Bomba 2** — comanda a Bomba 2 dentro das autorizações.

Esta é uma **arquitetura realista de planta pequena**: papéis claramente distintos, comunicação verbal entre operadores, supervisão de energia separada do controle de processo. A operação **deve respeitar pré-condições elétricas**: não dá para ligar uma bomba se o quadro está em sobre-tensão, ou se o limite de demanda foi atingido.

Esta é a **prática mais elaborada** do grupo. Vocês integrarão tudo o que aprenderam.

---

## 2. Distribuição de Papéis

| Aluno | Papel | Dispositivo que comanda | Smartphone |
|-------|-------|------------------------|-----------|
| **A** | **Operador de Energia / Painel** | Apenas medidor (read + write **somente configuração**) | Smartphone com MK-EM3P |
| **B** | **Operador da Bomba 1** | VFD-1 (read + write **comando e referência**) | Smartphone com MK-VFD7 |
| **C** | **Operador da Bomba 2** | VFD-2 (read + write **comando e referência**) | Smartphone com MK-VFD7 |

> **Cada operador comanda seu dispositivo. Todos veem todos os 3 dispositivos.** A coordenação acontece via **comunicação verbal** entre os operadores e via **políticas operacionais** documentadas.

---

## 3. Material Necessário

- **3 smartphones Android** com ModbusDeviceSIM (um para cada aluno)
- **3 laptops** com:
  - **Node-RED** + `node-red-contrib-modbus` + `node-red-dashboard`
  - **Python 3.10+** com pymodbus 3.x (para análise pós-evento)
- **Wi-Fi** comum aos 6 dispositivos
- (Opcional, mas recomendado) **Wireshark** em pelo menos um laptop para análise

---

## 4. Setup

### 4.1 Aluno A — Medidor de Energia

1. ModbusDeviceSIM → **MK-EM3P** → **START**.
2. Anote IP: `IP_EM3P = 192.168.1.50:5020`

### 4.2 Aluno B — Bomba 1

1. ModbusDeviceSIM → **MK-VFD7** → **START** → **REMOTE**.
2. Anote IP: `IP_VFD1 = 192.168.1.51:5020`

### 4.3 Aluno C — Bomba 2

1. ModbusDeviceSIM → **MK-VFD7** → **START** → **REMOTE**.
2. Anote IP: `IP_VFD2 = 192.168.1.52:5020`

### 4.4 Validação cruzada

Os 3 alunos testam ping para os 3 IPs do seu laptop. **6 pings** devem responder ao todo (3 alunos × 3 IPs, descontando o próprio IP local).

---

## 5. Política Operacional (Combine antes de começar)

**Esta é a peça central desta prática.** A equipe define **por escrito** as regras de operação:

### Regra 1 — Autorização de partida

> **Nenhuma bomba inicia sem autorização explícita do Operador de Energia.**
>
> O Operador A monitora o medidor. Se as condições elétricas estão OK (tensões dentro de faixa, alarmes apagados, potência total abaixo de 70 % do limite), ele dá **sinal verbal** ("VFD-1, autorizado a partir").

### Regra 2 — Limite de demanda

> **Potência total no quadro não pode exceder 15 kW** (limite arbitrário simulando contrato de fornecimento).
>
> O Operador A monitora. Se a potência se aproxima de 13 kW, ele alerta os operadores das bombas para **reduzirem frequência**.

### Regra 3 — Alarme elétrico = parada imediata

> **Se qualquer alarme do medidor disparar** (sobre-tensão, sub-tensão, sobre-corrente), **ambas as bombas devem parar imediatamente**.
>
> Cada operador de bomba **monitora o status do medidor** no seu próprio dashboard.

### Regra 4 — Comunicação verbal

> Toda mudança significativa (start, stop, fault, mudança de setpoint > 10 Hz) **deve ser comunicada verbalmente** aos outros operadores **antes** de ser executada.

---

## 6. Procedimento

### Etapa 1 — Cada Aluno Constrói Seu Dashboard (90 min)

Cada aluno desenvolve seu dashboard Node-RED com **foco na sua responsabilidade**.

#### 6.1 Servidores Modbus (cada aluno configura no seu Node-RED)

Os 3 alunos têm **3 servidores Modbus** configurados:

- `EM3P-Server`: host = IP do EM3P, porta 5020
- `VFD1-Server`: host = IP do VFD1, porta 5020
- `VFD2-Server`: host = IP do VFD2, porta 5020

#### 6.2 Aluno A — Dashboard de Energia

**Foco:** monitoração de energia + "semáforo" de autorização + configuração do medidor.

**Widgets:**

| Widget | Variável (registrador) | Tipo |
|--------|-----------------------|------|
| Gauge: Voltage L1-N | Reg 0–1, FC04 | FLOAT32 V |
| Gauge: Voltage L2-N | Reg 2–3 | FLOAT32 V |
| Gauge: Voltage L3-N | Reg 4–5 | FLOAT32 V |
| Gauge: Current L1 | Reg 12–13 | FLOAT32 A |
| Gauge: Current L2 | Reg 14–15 | FLOAT32 A |
| Gauge: Current L3 | Reg 16–17 | FLOAT32 A |
| **Gauge grande: Potência Total** | Reg 26–27 | FLOAT32 kW |
| Gauge: Frequency | Reg 52–53 | FLOAT32 Hz |
| Gauge: Power Factor | Reg 50–51 | FLOAT32 |
| Chart: 3 tensões nos últimos 5 min | — | — |
| Chart: Potência total nos últimos 15 min | — | — |
| Display: Alarm Status (bitmask decodificado) | Reg 90 | bits |
| Slider: CT Primary (config) | Reg 100, FC06 | UINT16 |
| Slider: Over-Voltage Threshold | Reg 107–108, FC16 | FLOAT32 |
| **Sinalizador "Semáforo de Operação"** (ui_template) | — | — |

**Semáforo de Operação** — uma ui_template:

```html
<style>
.traffic { padding:20px; border-radius:10px; text-align:center; color:#fff; font-weight:bold; font-size:1.5em }
</style>
<div ng-if="msg.payload.go" class="traffic" style="background:#1f5a1f">
    ✅ AUTORIZADO — Bombas podem operar
</div>
<div ng-if="msg.payload.caution" class="traffic" style="background:#5a4a1f">
    ⚠ ATENÇÃO — Próximo do limite
</div>
<div ng-if="msg.payload.stop" class="traffic" style="background:#5a1f1f">
    🛑 PARAR — Condição elétrica anormal
</div>
```

Function que calcula o semáforo (recebe `msg.payload` com dados decodificados do EM3P):

```javascript
const d = msg.payload;
const alarm = d.alarm_status || 0;
const power = d.p_total || 0;

let go = false, caution = false, stop = false;

if (alarm !== 0) {
    stop = true;  // qualquer alarme = parar tudo
} else if (power > 13.0) {
    caution = true;  // próximo do limite
} else if (power > 15.0) {
    stop = true;  // ultrapassou
} else {
    go = true;
}

msg.payload = { go, caution, stop, alarm, power };
return msg;
```

> **Os outros dois alunos verão esse semáforo no dashboard de energia. Mas cada um precisa replicar a lógica para o seu próprio painel.**

#### 6.3 Aluno B — Dashboard da Bomba 1

**Foco:** controle do VFD-1 + visibilidade da energia + indicador de autorização.

**Widgets do VFD-1 (controle):**

- Gauges: Frequency, Current, Speed
- LEDs: RUN, FWD, REV, REF, FAULT
- Botão START FWD / START REV / STOP / FAULT RESET
- Slider: Frequency Reference
- Chart histórico (5 min): Frequency

**Widgets do Medidor (observação):**

- Display: Potência Total (grande)
- Display: Status do semáforo de energia (replicado com a mesma lógica do Aluno A)
- LEDs: alarmes de OV, UV, OC do medidor

**Widgets do VFD-2 (observação, mínima):**

- Gauge pequeno: Frequency
- LED: RUN

> **Lógica importante**: antes de iniciar VFD-1, o Aluno B verifica visualmente no seu próprio dashboard que o semáforo de energia está VERDE.

#### 6.4 Aluno C — Dashboard da Bomba 2

**Idêntico ao do Aluno B**, mas controlando VFD-2 e observando VFD-1.

---

### Etapa 2 — Sequência de Partida Coordenada (45 min)

A equipe executa a partida da planta seguindo **as regras combinadas**:

**Passo 1 — Verificação inicial.**
- Aluno A confirma medidor está OK (todas as tensões em ~220 V, alarmes apagados, semáforo VERDE).
- Aluno A anuncia verbalmente: *"Energia OK. Bombas autorizadas a partir."*

**Passo 2 — Partida VFD-1.**
- Aluno B define **Frequency Reference = 30 Hz**.
- Aluno B anuncia: *"Iniciando Bomba 1 em 30 Hz."*
- Aluno B aperta **START FWD**.
- Todos observam:
  - Em seus dashboards, VFD-1 acelera.
  - O medidor (Aluno A) começa a registrar consumo de potência.
- Aluno A confirma: *"Bomba 1 consumindo ~3 kW. Energia ainda em verde."*

**Passo 3 — Partida VFD-2.**
- Aluno C define **Frequency Reference = 35 Hz**.
- Aluno C anuncia: *"Iniciando Bomba 2 em 35 Hz."*
- Aluno C aperta **START FWD**.
- Todos observam.
- Aluno A confirma: *"Potência total agora ~7 kW. Semáforo verde."*

**Passo 4 — Aumento de produção.**
- Aluno A anuncia: *"Demanda aumentou. Aumentem frequências."*
- Aluno B aumenta para **50 Hz**.
- Aluno C aumenta para **55 Hz**.
- Aluno A observa: *"Potência aproximando 13 kW. Semáforo AMARELO."*

**Passo 5 — Recuo coordenado.**
- Aluno A: *"Cuidado, próximo do limite. Recuem 5 Hz cada um."*
- Aluno B: *"OK, reduzindo VFD-1 para 45 Hz."*
- Aluno C: *"OK, reduzindo VFD-2 para 50 Hz."*
- Semáforo volta a VERDE.

**Passo 6 — Parada coordenada.**
- Aluno A: *"Finalizando operação. Parem as bombas em ordem inversa."*
- Aluno C para VFD-2.
- Aluno B para VFD-1.
- Energia volta a 0 kW.

---

### Etapa 3 — Cenário de Falha Elétrica Simulada (30 min)

Vocês irão simular uma sobre-tensão e observar a reação coordenada.

**Setup do cenário:**
- Equipe reinicia as bombas (Etapa 2 simplificada).
- Bomba 1 em 40 Hz. Bomba 2 em 45 Hz.

**Provocação da falha:**

- Aluno A altera **Over-Voltage Threshold** para um valor abaixo das tensões reais — por exemplo, 215 V.
- Use o slider no seu dashboard (ou EasyModbusTCP em paralelo).
- O EM3P registra a "sobre-tensão" (mesmo que a tensão real esteja em 220 V — porque o threshold ficou em 215 V).
- Alarm Status do medidor muda — bit 0 (OV) acende.
- O semáforo no dashboard do Aluno A vai para VERMELHO 🛑.

**Reação da equipe:**

- Aluno A grita: *"ALARME OV! Parem tudo!"*
- Alunos B e C **veem o alarme nos seus próprios dashboards** e param suas bombas imediatamente.
- Após confirmação de que tudo parou, Aluno A restaura o threshold para 253 V.
- Alarm Status zera.
- Semáforo volta a VERDE.
- Equipe pode retomar a operação.

> **Discussão:** essa reação foi puramente humana. Em uma planta real, seria automatizada via **interlock**. Como vocês implementariam isso?

---

### Etapa 4 — Automação do Interlock (45 min)

**Cenário:** vocês decidem **automatizar** a regra "alarme do medidor = parada imediata das bombas".

Cada operador de bomba (B e C) adiciona ao **seu próprio fluxo** Node-RED uma lógica que:

1. Lê o **Alarm Status** do EM3P (reg 90, FC04).
2. Se houver qualquer bit ligado, **envia automaticamente Stop ao seu VFD**.

Function node:

```javascript
const alarm = msg.payload[90];  // Alarm Status do EM3P
if (alarm !== 0) {
    msg.payload = 0;  // Stop (Control Word = 0)
    msg.alarm_alert = alarm;
    return msg;
}
return null;  // não envia nada se OK
```

Conecte a saída desse function a um **Modbus Write** que escreve no Control Word **do seu VFD** (reg 100, FC06).

> **Importante:** o Aluno A **não** precisa mudar nada — a inteligência do interlock está nos dashboards de B e C.

**Teste:** repitam o cenário da Etapa 3.
- Aluno A provoca alarme OV.
- **Sem aviso verbal**, os VFDs de B e C param **automaticamente**.
- Aluno A restaura threshold.
- B e C devem **reiniciar manualmente** (interlock não religa por segurança).

Compare:
- **Tempo de reação humana**: ~3-5 segundos
- **Tempo de reação automática**: ~1 ciclo de polling (~1 segundo)

---

### Etapa 5 — Logging Integrado em CSV (30 min)

Cada aluno adiciona um **file node** que gera um CSV unificado com **todos os dispositivos**.

Como cada laptop lê os 3 dispositivos, cada um gera um CSV com colunas tipo:

```
timestamp, em3p_v_l1, em3p_p_total, em3p_alarm, vfd1_freq, vfd1_status, vfd2_freq, vfd2_status
```

Após 20 minutos de operação (incluindo as etapas anteriores), cada aluno deve ter um CSV com **~1200 linhas** (a cada segundo).

---

### Etapa 6 — Análise Pós-Evento em Python (30 min)

Crie no laptop **um aluno** (decida quem) o script `analyze.py`:

```python
"""
Análise pós-evento dos CSVs combinados.
"""
import pandas as pd
import matplotlib.pyplot as plt

# Carrega o CSV
df = pd.read_csv("planta_log.csv", parse_dates=["timestamp"])

# Identifica evento de alarme (transição de 0 para != 0)
df["alarm_event"] = df["em3p_alarm"].diff() != 0

# Tempo entre alarme e parada da Bomba 1
alarm_times = df[df["alarm_event"]]["timestamp"]
stop_times  = df[df["vfd1_status"] == 0]["timestamp"]

# Plot integrado
fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
axes[0].plot(df["timestamp"], df["em3p_p_total"], label="Potência Total")
axes[0].axhline(15, color="r", linestyle="--", label="Limite 15 kW")
axes[0].set_ylabel("Potência (kW)")
axes[0].legend()

axes[1].plot(df["timestamp"], df["vfd1_freq"], label="VFD-1")
axes[1].plot(df["timestamp"], df["vfd2_freq"], label="VFD-2")
axes[1].set_ylabel("Frequência (Hz)")
axes[1].legend()

axes[2].plot(df["timestamp"], df["em3p_alarm"], label="Alarm Status (bitmask)")
axes[2].set_ylabel("Alarme")
axes[2].legend()

plt.tight_layout()
plt.savefig("analise_integrada.png", dpi=120)
plt.show()
```

Esse gráfico mostra a **timeline completa da operação**: potência consumida pelas bombas, frequência de cada VFD, e momentos de alarme.

---

### Etapa 7 — Apresentação Final (15 min)

A equipe junta tudo e apresenta em conjunto:

1. **Demo ao vivo**: executem novamente a sequência completa (Etapa 2 + Etapa 3) na frente do professor.
2. **Mostrem os 3 dashboards** sincronizados.
3. **Discutam** o cenário de falha (Etapa 3) vs. automatizado (Etapa 4).
4. **Mostrem o gráfico integrado** da Etapa 6.

---

## 7. Critérios de Sucesso

A equipe completou esta prática se:

- ✅ Os 3 dashboards estão funcionando e mostrando dados corretos.
- ✅ O **semáforo de operação** no dashboard do Aluno A muda conforme as condições.
- ✅ A **sequência de partida coordenada** (Etapa 2) foi executada com sucesso.
- ✅ O **cenário de falha manual** (Etapa 3) demonstrou reação coordenada da equipe.
- ✅ O **interlock automatizado** (Etapa 4) **parou as bombas automaticamente** ao detectar alarme.
- ✅ Cada aluno gerou um **CSV integrado** com pelo menos 20 minutos de dados.
- ✅ O **gráfico integrado** (Etapa 6) mostra a correlação entre potência total, frequências das bombas e eventos de alarme.

---

## 8. Discussão e Reflexão

A equipe responde coletivamente:

1. **Hierarquia de controle.** Esta prática tem uma **clara hierarquia**: Aluno A "autoriza", B e C "executam". Discutam quais decisões devem ser **automáticas** e quais devem ser **humanas** em uma planta real. Quando o automatismo é arriscado?
2. **Latência da reação coordenada.** Comparem (com dados dos CSVs):
   - Tempo entre alarme do medidor e parada de cada bomba na **Etapa 3 (manual)**
   - Tempo na **Etapa 4 (automatizado)**
   Discutam: quanta latência é aceitável em alarmes elétricos? Em que pontos automatizar é **mandatório**?
3. **Falha do interlock.** No interlock automatizado da Etapa 4, **cada operador de bomba leu o EM3P do seu laptop**. Se o laptop do Aluno B trava, o VFD-1 NÃO recebe o sinal de parada. Em uma planta real, onde **deve residir** essa lógica de interlock? Justifiquem.
4. **Modbus TCP no contexto.** Comparem a operação que vocês fizeram com a hipótese de usar **Modbus RTU** (serial). Por que essa arquitetura **só faz sentido sobre TCP**?
5. **Cibersegurança.** Atualmente, qualquer dispositivo na rede Wi-Fi pode ler e escrever nos VFDs. Como vocês protegeriam essa planta contra:
   - Acesso não autorizado da rede corporativa?
   - Comandos maliciosos vindos de fora?
   - Spoofing de identidade?
6. **Escalabilidade.** Imaginem que a planta cresce: 5 bombas, 2 medidores, 1 banco de geradores. Como vocês adaptariam a arquitetura desta prática? Quando o **dashboard distribuído** (como vocês fizeram) deixa de funcionar e é preciso um **SCADA centralizado**?

---

## 9. Entregáveis (equipe)

**Um único relatório de equipe consolidado** contendo:

1. **Documento "Política Operacional"** (1 página) com as 4 regras combinadas no início, em formato formal.
2. **Diagrama da arquitetura**: 3 smartphones (com IPs), 3 laptops (com responsabilidades), Wi-Fi.
3. **Os 3 dashboards Node-RED exportados** (JSON), um por aluno.
4. **Screenshots simultâneos** (4 momentos diferentes):
   - Planta parada
   - Operação normal (ambas bombas rodando)
   - Próximo do limite (semáforo amarelo)
   - Alarme ativo (semáforo vermelho, interlock disparado)
5. **CSVs** dos 3 alunos com pelo menos 20 minutos de dados (idealmente cobrindo as Etapas 2, 3 e 4).
6. **Gráfico integrado** (PNG ou PDF) gerado em Python (Etapa 6).
7. **Análise quantitativa**:
   - Tempo médio de reação manual (Etapa 3)
   - Tempo médio de reação automática (Etapa 4)
   - Potência máxima atingida durante operação
   - Número de eventos de alarme registrados
8. **Vídeo (5–8 min)** mostrando a operação coordenada completa, narrada pelos 3 alunos explicando seus papéis em tempo real.
9. **Respostas** às 6 perguntas da seção 8 (1–2 parágrafos cada).

---

## 10. Solução de Problemas

| Sintoma | Causa | Solução |
|---------|-------|---------|
| Interlock automatizado não dispara | Lógica do function incorreta | Verifique condição `alarm !== 0` |
| Semáforo do Aluno A oscila entre verde/amarelo | Potência oscilando perto do limite | Adicione histerese (verde até 12 kW, amarelo de 13 a 14, vermelho > 15) |
| Alarme provocado não é registrado | Threshold escrito no lugar errado | Confirme endereço 107–108 do EM3P |
| Bombas não param ao alarme | Modbus Write apontando para servidor errado | Confirme que cada aluno escreve no SEU VFD |
| CSVs divergem muito entre os 3 alunos | Timing de polling diferente | Esperado; defasagem de ~1s é normal |
| Dashboards travam ao crescer muito | Muitos charts | Reduza para apenas variáveis essenciais |

---

## 11. Considerações Finais

Esta prática **consolida toda a disciplina**. Vocês passaram de:
- Manipular bits em uma porta serial (Módulos 2-4)
- Para decodificar frames Modbus RTU (Módulo 6)
- Para entender TCP/IP (Módulo 8)
- Para implementar Modbus TCP em ferramentas variadas (Práticas 1-6)
- Para coordenar 3 operadores em uma planta integrada com automação e supervisão humana (esta prática)

Em sua carreira, vocês raramente programarão **um único equipamento**. A maioria dos sistemas industriais são **integrações** — vários dispositivos, vários protocolos, vários usuários. As lições desta prática:

- **Convenções operacionais** importam tanto quanto código
- **Comunicação humana** complementa (e não substitui) a automação
- **Latência** é uma realidade técnica que limita o que pode ser feito em tempo real
- **Arquiteturas distribuídas** trazem resiliência mas exigem disciplina
- **Cibersegurança** entra cedo no projeto, não no final

Levem essas lições adiante.

---

## 12. Critérios de Avaliação Detalhados

| Critério | Peso |
|----------|------|
| Funcionamento técnico (todas as etapas concluídas) | 30% |
| Política operacional bem definida e seguida | 10% |
| Qualidade dos 3 dashboards (interfaces adequadas aos papéis) | 15% |
| Interlock automatizado funcionando | 10% |
| Logging e análise pós-evento (incluindo gráfico integrado) | 15% |
| Apresentação e demo coletiva | 10% |
| Discussões e respostas às 6 perguntas | 10% |

---

**Parabéns por completarem a disciplina.**

— **Prof. Dênis Leite**
*Mekatronik — Advanced Engineering*
