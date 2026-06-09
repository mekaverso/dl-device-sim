# Prática Grupo 3 — 3 Clientes Operando 3 VFDs

> *"Cada operador comanda seu próprio motor — mas todos enxergam o sistema inteiro. É assim que plantas modernas funcionam."*

## 1. Contexto Industrial

Em uma fábrica com várias estações de trabalho independentes, é comum que **cada operador** tenha sua própria HMI controlando **sua máquina**, enquanto vê — em modo somente leitura — as **outras máquinas da planta**. Exemplos:

- **Linha de embalagem segmentada**: cada operador controla uma seção
- **Pátio de tanques**: cada turno gerencia tanques específicos
- **Estações de teste**: cada bancada opera independentemente, mas comparte ambiente

A vantagem dessa arquitetura:

- **Responsabilidade clara**: cada operador é dono de sua máquina
- **Visibilidade global**: todos sabem o que está ocorrendo no resto da planta
- **Sem ponto único de falha**: se um sistema cai, os outros continuam operando
- **Sem race condition de comandos**: cada VFD tem **um único cliente que escreve**, mas múltiplos que leem

Esta prática implementa exatamente isso: **3 estações de operação independentes**, cada uma com seu próprio VFD e seu próprio operador, mas com **visibilidade compartilhada**.

---

## 2. Distribuição de Papéis

A equipe de **3 alunos** se organiza assim:

| Aluno | Papel | Comanda | Vê |
|-------|-------|---------|-----|
| **A** | Operador VFD-1 | VFD-1 (read+write) | Todos os 3 |
| **B** | Operador VFD-2 | VFD-2 (read+write) | Todos os 3 |
| **C** | Operador VFD-3 | VFD-3 (read+write) | Todos os 3 |

> Cada aluno é **autoridade de escrita** sobre **um único VFD**. Os demais têm acesso ao mesmo VFD, mas **por convenção** só leem (Modbus TCP não impede tecnicamente — é uma regra organizacional).

> **Não há rotação obrigatória nesta prática** — todos exercem o mesmo papel. A diferença está em cada aluno **comandar seu próprio VFD ao mesmo tempo** que os outros comandam os deles.

---

## 3. Material Necessário

- **3 smartphones Android** com ModbusDeviceSIM
- **3 laptops**, cada um com Node-RED, `node-red-contrib-modbus`, `node-red-dashboard`
- **Python 3.10+** com pymodbus 3.x (para validação inicial)
- Wi-Fi comum

---

## 4. Setup

### 4.1 Os 3 smartphones

Cada aluno configura **seu próprio smartphone**:

1. Abre ModbusDeviceSIM, seleciona **MK-VFD7**, **START**.
2. **Modo REMOTE**.
3. Anota o IP.

A equipe registra:

```
   VFD-1 (Aluno A): IP = 192.168.1.51:5020
   VFD-2 (Aluno B): IP = 192.168.1.52:5020
   VFD-3 (Aluno C): IP = 192.168.1.53:5020
```

### 4.2 Os 3 laptops

Cada aluno faz no seu laptop:

1. Abre Node-RED.
2. Confirma que os módulos `modbus` e `dashboard` estão instalados.
3. Testa ping para os 3 IPs (não só o próprio).

---

## 5. Conceitos Necessários

### 5.1 Arquitetura

```
            ┌─────────────────────────────────────────┐
            │                                         │
            │   SMARTPHONE 1 (VFD-1)                  │
            │   SMARTPHONE 2 (VFD-2)                  │
            │   SMARTPHONE 3 (VFD-3)                  │
            │                                         │
            └──────────┬──────────────────────────────┘
                       │
              ┌────────┼──────────┐
              │        │          │
        ┌─────▼─┐  ┌───▼───┐  ┌──▼────┐
        │Aluno A│  │Aluno B│  │Aluno C│
        │       │  │       │  │       │
        │Lê 1,2,3│ │Lê 1,2,3│ │Lê 1,2,3│
        │Escreve│  │Escreve│  │Escreve│
        │em 1   │  │em 2   │  │em 3   │
        └───────┘  └───────┘  └───────┘
```

Cada laptop conecta-se a **3 servidores Modbus TCP** (os 3 VFDs).

### 5.2 Registradores essenciais

(Iguais ao MK-VFD7 das práticas anteriores.)

| Endereço | Variável             | Tipo    | Acesso |
|----------|----------------------|---------|--------|
| 0–1      | Output Frequency     | FLOAT32 | R      |
| 4–5      | Output Current       | FLOAT32 | R      |
| 8–9      | Motor Speed          | FLOAT32 | R      |
| 26       | Drive Status         | UINT16  | R      |
| 100      | Control Word         | UINT16  | R/W    |
| 101–102  | Frequency Reference  | FLOAT32 | R/W    |

---

## 6. Procedimento

### Etapa 1 — Validação Prévia em Python (15 min)

**Cada aluno** roda um script de validação para confirmar que consegue ler todos os 3 VFDs do seu laptop.

Crie `01_validate.py`:

```python
"""
Etapa 1: cada aluno valida que consegue ler os 3 VFDs.
"""
from pymodbus.client import ModbusTcpClient
import struct

VFDS = {
    "VFD1": "192.168.1.51",
    "VFD2": "192.168.1.52",
    "VFD3": "192.168.1.53",
}


def words_to_float(h, l):
    return struct.unpack(">f", struct.pack(">HH", h, l))[0]


for name, host in VFDS.items():
    c = ModbusTcpClient(host, port=5020, timeout=2.0)
    if not c.connect():
        print(f"  ❌ {name} ({host}): falha de conexão")
        continue
    r = c.read_input_registers(address=0, count=29, device_id=1)
    if r.isError():
        print(f"  ❌ {name} ({host}): erro de leitura")
    else:
        freq = words_to_float(r.registers[0], r.registers[1])
        running = bool(r.registers[26] & 0x0001)
        print(f"  ✓ {name} ({host}): f={freq:.2f}Hz RUN={running}")
    c.close()
```

Execute. Os 3 alunos devem conseguir ler os 3 VFDs do seu próprio laptop.

**Verifique nos smartphones:** se os 3 alunos rodam o script ao mesmo tempo, **cada smartphone deve mostrar até 3 clientes** brevemente.

---

### Etapa 2 — Dashboard Individual (60 min)

**Cada aluno** constrói seu dashboard Node-RED. A estrutura é a mesma para todos, **mas com uma seção destacada para "o meu VFD"** (com controles) e duas seções **read-only** para os outros 2 VFDs.

#### 2.1 Servidores Modbus

Cada aluno configura **3 servidores Modbus** no seu Node-RED:

- `VFD-1`: host = IP do smartphone 1, porta 5020
- `VFD-2`: host = IP do smartphone 2, porta 5020
- `VFD-3`: host = IP do smartphone 3, porta 5020

#### 2.2 Fluxo de leitura para cada VFD

Para cada um dos 3 servidores, crie:

```
   [Inject 1s] → [Modbus Read FC04, addr 0, qty 29] → [function decodifica] → [link out: VFD-N]
```

O function de decodificação (cole nos 3, ajustando `msg.topic`):

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
    name: msg.topic,
    frequency: f32(regs[0], regs[1]),
    current: f32(regs[4], regs[5]),
    speed: f32(regs[8], regs[9]),
    running: !!(s & 0x0001),
    forward: !!(s & 0x0002),
    reverse: !!(s & 0x0004),
    at_reference: !!(s & 0x0008),
    fault: !!(s & 0x0040),
};
return msg;
```

Adicione um **change** após o function para setar `msg.topic = "VFD1"` (ou VFD2/VFD3 conforme o fluxo).

#### 2.3 Dashboard — "Meu VFD" (com controles)

Crie um **grupo destacado** no dashboard chamado `"MEU VFD (VFD-X)"` (X = 1, 2 ou 3 conforme o aluno).

Inclua nele:

- Gauge: Frequency
- Gauge: Current
- Gauge: Motor Speed
- LEDs virtuais: RUN, FWD, REV, REF, FAULT
- Botão: START FWD
- Botão: START REV
- Botão: STOP
- Botão: FAULT RESET
- Slider: Frequency Reference (0–60 Hz)

Os botões e slider escrevem **apenas no SEU VFD**. Configure-os para usar o servidor Modbus correto.

#### 2.4 Dashboards "Outros VFDs" (read-only)

Crie 2 grupos, um para cada VFD que **não é o seu**:

- `"VFD-Y (apenas observação)"`
- `"VFD-Z (apenas observação)"`

Inclua:
- Gauges: Frequency, Current (menores que os do seu VFD, para indicar prioridade visual)
- LEDs: RUN, FAULT
- (Opcional) Chart histórico pequeno

> **Importante:** estes grupos **não têm botões nem sliders**. São observação pura.

#### 2.5 Identificação visual

Adicione um banner colorido no topo:

```html
<div style="background:#0066ff; color:#fff; padding:10px; border-radius:6px; text-align:center; font-weight:bold">
    Estação Aluno A — Controla VFD-1
</div>
```

(Cores sugeridas: Aluno A azul, Aluno B verde, Aluno C laranja)

---

### Etapa 3 — Operação Paralela Independente (30 min)

**Os 3 alunos operam simultaneamente seus VFDs**, **sem coordenação prévia**, simulando 3 estações independentes:

1. **Aluno A** define VFD-1 em 35 Hz, start forward.
2. **Aluno B** simultaneamente define VFD-2 em 50 Hz, start forward.
3. **Aluno C** simultaneamente define VFD-3 em 25 Hz, start reverse.

**Cada aluno** observa em **seu próprio dashboard**:
- Seu VFD (controlado) responde aos seus comandos.
- Os outros 2 VFDs (read-only) mostram a operação dos colegas em tempo real.

**Verificação:** quando o Aluno B muda a frequência do VFD-2 para 30 Hz, **os outros 2 alunos veem essa mudança nos seus dashboards** (pequeno atraso de polling).

---

### Etapa 4 — Cenários Coordenados (Combinados Verbalmente) (45 min)

Agora a equipe coordena verbalmente cenários de operação. Não há automação central — **apenas comunicação humana** entre os alunos.

#### Cenário 1 — Sincronia visual

A equipe combina:
- "Vamos os 3 acelerar nossos VFDs simultaneamente, em 3-2-1."
- No "GO", cada aluno aperta START FWD.
- Observam: os 3 dashboards mostram os 3 VFDs subindo ao mesmo tempo.
- Discutem: há alguma vantagem operacional em sincronismo? Em quais aplicações?

#### Cenário 2 — Sequência colaborativa

A equipe combina uma sequência:
1. Aluno A inicia VFD-1.
2. Quando Aluno B vê VFD-1 em referência (LED REF aceso) no seu dashboard, ele inicia VFD-2.
3. Quando Aluno C vê VFD-2 em referência, ele inicia VFD-3.

> Esse é o equivalente "humano" da partida sequencial que vocês implementaram automaticamente na **Prática Grupo 2**. Compare a experiência.

#### Cenário 3 — Reação a falha

A equipe combina: "Se algum de nós ver fault em outro VFD, vamos parar o nosso também (procedimento de segurança simulado)."

- Aluno A propositalmente provoca uma falha no seu VFD-1 (rebaixe o threshold de Over-Current via outra ferramenta).
- VFD-1 entra em fault.
- Alunos B e C veem nos seus dashboards o fault em VFD-1 e param seus próprios VFDs.
- Aluno A faz fault reset.
- A equipe reinicia coordenadamente.

#### Cenário 4 — Tentativa de "intrusão"

Conforme combinado:
- Aluno A tenta enviar um comando para VFD-2 (não é o seu, mas tecnicamente pode).
- Construam temporariamente no dashboard do Aluno A um botão extra que escreve no servidor VFD-2.
- Aluno A pressiona. Aluno B vê seu VFD reagir sem ter sido ele que comandou.
- Discutam: como evitar isso em uma planta real?

---

### Etapa 5 — Logging Independente e Consolidação (30 min)

Cada aluno adiciona ao seu fluxo Node-RED um **file** node que gera um CSV com timestamp das leituras dos **3 VFDs**:

```javascript
const d = msg.payload;
// Espera-se que msg.payload tenha {VFD1: {...}, VFD2: {...}, VFD3: {...}}
const ts = new Date().toISOString();
const line = [
    ts,
    d.VFD1?.frequency?.toFixed(2), d.VFD1?.current?.toFixed(2), d.VFD1?.running,
    d.VFD2?.frequency?.toFixed(2), d.VFD2?.current?.toFixed(2), d.VFD2?.running,
    d.VFD3?.frequency?.toFixed(2), d.VFD3?.current?.toFixed(2), d.VFD3?.running,
].join(",");
msg.payload = line;
return msg;
```

Para isso, agregue antes os 3 fluxos em um único objeto. Use a função `join` em um **change** ou agregue via context global:

```javascript
const cur = global.get("latest") || {};
cur[msg.payload.name] = msg.payload;
global.set("latest", cur);
if (cur.VFD1 && cur.VFD2 && cur.VFD3) {
    msg.payload = cur;
    return msg;
}
return null;
```

Cada aluno gera **seu próprio CSV** (`logs/operador_A.csv`, etc.).

Após **15 min de operação**, comparem os 3 CSVs. Devem ser muito similares.

---

### Etapa 6 — Análise Coletiva (15 min)

A equipe se reúne com os 3 CSVs abertos lado a lado (em planilha ou Python):

1. **Sincronização temporal**: para um evento conhecido (ex.: Aluno A iniciou VFD-1 às 14:25:30), em quais segundos cada um dos 3 CSVs registra a mudança?
2. **Consistência de valores**: os valores de Frequency lidos nos 3 CSVs para um mesmo VFD em um mesmo momento são iguais?
3. **Independência**: as operações de cada aluno apareceram corretamente nos logs dos outros?

---

## 7. Critérios de Sucesso

A equipe completou esta prática se:

- ✅ Cada aluno construiu **um dashboard Node-RED** com seu próprio VFD destacado (controles) e os outros 2 em modo observação.
- ✅ Os 3 alunos operaram **simultaneamente** seus VFDs sem conflito.
- ✅ Pelo menos **3 cenários coordenados** (Sincronia, Sequência, Falha) foram executados.
- ✅ Cada aluno gerou um **CSV de 15 min** com os 3 VFDs sincronizados.
- ✅ A equipe **consolidou** os logs e analisou consistência.

---

## 8. Discussão e Reflexão

1. **Convenção vs. proteção técnica.** No Cenário 4 da Etapa 4, vocês demonstraram que **nada impede** um operador de comandar o VFD "do outro". Em uma planta real, como esse problema é mitigado? Pesquisem:
   - **Modbus TCP Security** (especificação 2018)
   - **Network segmentation** (VLANs separadas por estação)
   - **Application-level locks** em SCADAs profissionais
2. **Coordenação humana vs. automação.** Comparem a experiência do Cenário 2 (sequência humana) com a partida sequencial automatizada da **Prática Grupo 2**. Quais as vantagens e desvantagens de cada uma?
3. **Visibilidade compartilhada.** Em uma planta com **50 estações**, cada uma vendo todas as outras é viável? Discutam:
   - Sobrecarga de UI (50 grupos no dashboard?)
   - Latência (a cada laptop fazer 50 conexões Modbus?)
   - Alternativas: dashboard centralizado vs. distribuído
4. **Isolamento de falhas.** O que aconteceria se **o laptop do Aluno A travasse** durante operação? Vocês verificaram que os Alunos B e C continuariam operando. Discutam **arquiteturas tolerantes a falhas**.
5. **Reflexão.** Em qual cenário desta prática vocês mais "sentiram" a importância da **boa comunicação humana**? Que paralelo isso tem com plantas reais?

---

## 9. Entregáveis (equipe)

Um relatório consolidado contendo:

1. **Diagrama** da arquitetura: 3 smartphones + 3 laptops + papéis de cada aluno.
2. **3 dashboards exportados** (JSON do Node-RED) — um por aluno.
3. **Screenshot múltiplo**: os 3 dashboards lado a lado em pelo menos 2 momentos da operação.
4. **3 arquivos CSV** (um por aluno) com pelo menos 15 minutos cobrindo as operações conjuntas.
5. **Análise de sincronização**: gráfico (matplotlib ou Excel) mostrando, na mesma timeline, a frequência de VFD-1 conforme registrada nos 3 CSVs.
6. **Vídeo (3-5 min)** mostrando a operação coordenada dos cenários da Etapa 4.
7. **Respostas** às 5 perguntas da seção 8.

---

## 10. Solução de Problemas

| Sintoma | Causa | Solução |
|---------|-------|---------|
| Aluno só vê seu VFD, não os outros | Faltou configurar os 3 servidores Modbus | Crie todos os 3 servers no Node-RED |
| Botões do Aluno A operam VFD do Aluno B | Configurou Modbus Write com server errado | Verifique cada write — server correto |
| Smartphone do colega trava | Memória baixa | Mantenha tela acesa; feche apps em segundo plano |
| Dashboards mostram valores diferentes para o mesmo VFD | Pequena defasagem temporal | Esperado; aceite alguns segundos de diferença |
| Comando do colega aparece com atraso no meu dashboard | Polling de 1s | Diminua intervalo (mas cuidado com carga) |

---

## 11. Próxima Prática

- **[Prática Grupo 4 — Mini-planta integrada](11-pratica-grupo-4-mini-planta.md)**: a culminação — 2 VFDs + 1 medidor com papéis distintos e coordenação realista.

---

**Boa operação distribuída!**

— **Prof. Dênis Leite**
*Mekatronik — Advanced Engineering*
