# Prática 7 — Multi-dispositivos em Grupo

> *"Sua primeira planta — pequena, mas distribuída. Três alunos, três smartphones, três laptops, um único sistema."*

## 1. Contexto Industrial

Plantas industriais reais **nunca** consistem em um único equipamento. São **dezenas a centenas** de dispositivos comunicando simultaneamente:

- Medidores de energia em cada quadro
- Inversores controlando motores em cada subsistema
- CLPs orquestrando sequências
- HMIs em cada estação de operação
- Servidores SCADA centralizando histórico
- Manutenção acessando remotamente

**Múltiplos clientes acessando múltiplos servidores ao mesmo tempo** é a realidade do dia a dia. E é onde Modbus TCP se diferencia do RTU: **suporta concorrência nativa**.

Nesta prática, vocês — uma equipe de **3 alunos** — irão simular uma pequena estação de bombeamento com:

- **1 medidor de energia** (quadro geral)
- **2 inversores de frequência** controlando 2 bombas
- **3 estações de monitoração** (cada aluno em seu laptop) que acessam todos os 3 dispositivos

Vocês também implementarão **lógica coordenada**: se o medidor detecta sobre-corrente no quadro, **as duas bombas reduzem velocidade** automaticamente — uma estratégia simples de proteção de circuito que existe em plantas reais.

---

## 2. Conceitos Necessários

### 2.1 Concorrência em Modbus TCP

Modbus TCP suporta **múltiplos clientes simultâneos** conectados ao mesmo servidor. Cada cliente abre uma conexão TCP independente. O servidor processa requisições em paralelo (até o limite configurado).

> **No ModbusDeviceSIM**, o servidor aceita até **5 clientes simultâneos**.

### 2.2 Coordenação de escrita

Quando múltiplos clientes podem escrever no mesmo registrador, surge o problema clássico de **race conditions** (condições de corrida). **A última escrita ganha** — o servidor não tem mecanismo de "trava".

Boas práticas:

- **Designar um cliente "mestre"** para comandos críticos
- Usar **Reads frequentes** para confirmar que o estado está como esperado
- Implementar **lógica de heartbeat** ou **lease** quando vários clientes podem comandar

### 2.3 Mapas de Registradores

Para esta prática, vocês precisarão dos mapas dos dois dispositivos. Resumo:

**MK-EM3P (Medidor de Energia):**
- Reg 0–1: Voltage L1-N (FLOAT32)
- Reg 12–13: Current L1 (FLOAT32)
- Reg 26–27: Active Power Total (FLOAT32)
- Reg 90: Alarm Status (UINT16 bitmask)

**MK-VFD7 (Inversor):**
- Reg 0–1: Output Frequency (FLOAT32)
- Reg 4–5: Output Current (FLOAT32)
- Reg 26: Drive Status (UINT16 bitmask)
- Reg 100: Control Word (UINT16)
- Reg 101–102: Frequency Reference (FLOAT32)

---

## 3. Material Necessário

Para a equipe de 3 alunos:

- **3 smartphones Android**, cada um com **ModbusDeviceSIM** instalado
- **3 laptops** com:
  - **Node-RED** instalado (todos os 3 alunos)
  - **Python 3.10+** com pymodbus (todos os 3 alunos)
  - **EasyModbusTCP** (para diagnóstico)
  - **Wireshark** (recomendado, ao menos 1 laptop)
- **Conexão Wi-Fi** comum a todos os 6 dispositivos

> ⚠️ **Importante:** todos os smartphones e laptops precisam estar na **mesma sub-rede**. Verifique antes de começar.

---

## 4. Setup Inicial

### 4.1 Distribuição de Papéis

A equipe define **um papel para cada aluno**:

| Aluno | Smartphone simula | Foco no laptop |
|-------|-------------------|----------------|
| **Aluno 1** | **MK-EM3P** (medidor) | Coleta + lógica coordenada |
| **Aluno 2** | **MK-VFD7** (Bomba 1) | HMI + controle local |
| **Aluno 3** | **MK-VFD7** (Bomba 2) | HMI + controle local |

> Cada aluno é "dono" de um dispositivo, mas **todos os 3 laptops** monitoram **todos os 3 dispositivos**. Cada um implementa seu próprio dashboard.

### 4.2 Setup dos Dispositivos

**Aluno 1 — Medidor de Energia:**
1. Abra ModbusDeviceSIM, selecione **MK-EM3P**, **START**.
2. Anote o IP — exemplo: `IP_EM3P = 192.168.1.10:5020`.

**Aluno 2 — Bomba 1 (VFD):**
1. Abra ModbusDeviceSIM, selecione **MK-VFD7**, **START**.
2. **Modo REMOTE.**
3. Anote o IP — exemplo: `IP_VFD1 = 192.168.1.11:5020`.

**Aluno 3 — Bomba 2 (VFD):**
1. Abra ModbusDeviceSIM, selecione **MK-VFD7**, **START**.
2. **Modo REMOTE.**
3. Anote o IP — exemplo: `IP_VFD2 = 192.168.1.12:5020`.

### 4.3 Validação de Conectividade

**Cada aluno** abre o terminal e testa:

```
ping <IP_EM3P>
ping <IP_VFD1>
ping <IP_VFD2>
```

Os 3 pings devem responder. **Se algum falhar, resolva antes de prosseguir.**

---

## 5. Procedimento

### Etapa 1 — Verificação Multi-cliente Simples (15 min)

**Objetivo:** confirmar que múltiplos laptops conseguem acessar o mesmo dispositivo simultaneamente.

**Cada aluno**, abra **EasyModbusTCP** e conecte-se ao **MK-EM3P** (Aluno 1).

**Verifique no smartphone do Aluno 1:** o contador **Clients** deve mostrar **3**.

**Cada aluno** faça uma leitura FC04 dos registradores 0–10. Compare os valores entre os 3 laptops — devem ser **idênticos** (ou muito próximos, dado o tempo entre as leituras).

✓ **Sucesso parcial:** vocês confirmaram concorrência multi-cliente.

---

### Etapa 2 — Cliente Python Multi-dispositivo (30 min)

**Objetivo:** cada aluno implementa um cliente Python que lê **todos os 3 dispositivos** simultaneamente.

Crie no laptop de cada aluno o arquivo `multi_client.py`:

```python
"""
Prática 7 — Etapa 2: cliente que polla 3 dispositivos.
"""
from pymodbus.client import ModbusTcpClient
import struct
import time

# === Substitua pelos IPs reais ===
EM3P_HOST = "192.168.1.10"
VFD1_HOST = "192.168.1.11"
VFD2_HOST = "192.168.1.12"
PORT = 5020


def words_to_float(h, l):
    return struct.unpack(">f", struct.pack(">HH", h, l))[0]


def read_em3p(client):
    r = client.read_input_registers(address=0, count=92, device_id=1)
    if r.isError():
        return None
    return {
        "v_l1": words_to_float(r.registers[0], r.registers[1]),
        "v_l2": words_to_float(r.registers[2], r.registers[3]),
        "v_l3": words_to_float(r.registers[4], r.registers[5]),
        "i_l1": words_to_float(r.registers[12], r.registers[13]),
        "i_l2": words_to_float(r.registers[14], r.registers[15]),
        "i_l3": words_to_float(r.registers[16], r.registers[17]),
        "p_total": words_to_float(r.registers[26], r.registers[27]),
        "alarm_status": r.registers[90],
    }


def read_vfd(client):
    r = client.read_input_registers(address=0, count=29, device_id=1)
    if r.isError():
        return None
    return {
        "frequency": words_to_float(r.registers[0], r.registers[1]),
        "current":   words_to_float(r.registers[4], r.registers[5]),
        "speed":     words_to_float(r.registers[8], r.registers[9]),
        "status":    r.registers[26],
        "running":   bool(r.registers[26] & 0x0001),
        "fault":     bool(r.registers[26] & 0x0040),
    }


def main():
    em = ModbusTcpClient(EM3P_HOST, port=PORT, timeout=2.0)
    v1 = ModbusTcpClient(VFD1_HOST, port=PORT, timeout=2.0)
    v2 = ModbusTcpClient(VFD2_HOST, port=PORT, timeout=2.0)

    em.connect()
    v1.connect()
    v2.connect()

    try:
        for i in range(20):
            em_data = read_em3p(em)
            v1_data = read_vfd(v1)
            v2_data = read_vfd(v2)

            print(f"\n--- Iteração {i+1} ---")
            if em_data:
                print(f"EM3P:  V_l1={em_data['v_l1']:.1f}V  P={em_data['p_total']:.2f}kW  "
                      f"I_l1={em_data['i_l1']:.1f}A  alarm=0x{em_data['alarm_status']:04X}")
            if v1_data:
                print(f"VFD1:  f={v1_data['frequency']:.1f}Hz  I={v1_data['current']:.2f}A  "
                      f"speed={v1_data['speed']:.0f}RPM  {'RUN' if v1_data['running'] else 'STOP'}")
            if v2_data:
                print(f"VFD2:  f={v2_data['frequency']:.1f}Hz  I={v2_data['current']:.2f}A  "
                      f"speed={v2_data['speed']:.0f}RPM  {'RUN' if v2_data['running'] else 'STOP'}")

            time.sleep(2)
    finally:
        em.close(); v1.close(); v2.close()


if __name__ == "__main__":
    main()
```

**Cada aluno** executa simultaneamente. **Verifique no smartphone do Aluno 1**: o contador deve mostrar **3 clientes** (um de cada laptop).

**Verifique nos smartphones dos Alunos 2 e 3:** também 3 clientes.

✓ **Sucesso da Etapa 2:** os 9 fluxos de leitura (3 laptops × 3 dispositivos) operam simultaneamente sem conflito.

---

### Etapa 3 — Comandos Coordenados (30 min)

**Objetivo:** demonstrar que cada laptop pode também comandar os inversores.

**Cada aluno**, escreva e execute:

```python
"""
Prática 7 — Etapa 3: comando coordenado.
Cada aluno definirá uma frequência diferente para uma das bombas.
"""
from pymodbus.client import ModbusTcpClient
import struct, time

VFD1_HOST = "192.168.1.11"
PORT = 5020


def float_to_words(value):
    return struct.unpack(">HH", struct.pack(">f", value))


# Cada aluno escolhe uma frequência diferente
# Aluno 1: 20 Hz
# Aluno 2: 30 Hz
# Aluno 3: 40 Hz
TARGET_FREQ = 30.0  # ALTERE conforme o seu papel

c = ModbusTcpClient(VFD1_HOST, port=PORT)
c.connect()

# Define referência
hi, lo = float_to_words(TARGET_FREQ)
c.write_registers(address=101, values=[hi, lo], device_id=1)

# Pequena pausa para todos sincronizarem
print(f"Definindo VFD1 para {TARGET_FREQ} Hz")
time.sleep(0.5)

# Inicia
c.write_register(address=100, value=1, device_id=1)
print("Comando RUN enviado")

c.close()
```

**Os 3 alunos executam ao mesmo tempo (combine 3, 2, 1, GO).**

**Observem o smartphone do VFD1:**
- A frequência reference muda 3 vezes em rápida sucessão.
- A última escrita **vence** — qual frequência ficou ativa?

**Discussão:** vocês acabam de encontrar **na prática** o problema de race condition. Em uma planta real, isso seria **muito perigoso**.

**Como mitigar?** Combine na equipe: **apenas 1 cliente** comanda os VFDs (Aluno 2 controla Bomba 1, Aluno 3 controla Bomba 2). Os demais apenas **observam**.

---

### Etapa 4 — Implementar Dashboards Independentes em Node-RED (60 min)

**Objetivo:** **cada aluno** constrói seu próprio fluxo Node-RED que monitora os 3 dispositivos. Os 3 dashboards devem mostrar **as mesmas informações de forma consistente**.

**Cada aluno**:

1. Abra Node-RED.
2. Configure **3 servidores Modbus**:
   - `EM3P-Server`: IP do medidor, porta 5020
   - `VFD1-Server`: IP da Bomba 1, porta 5020
   - `VFD2-Server`: IP da Bomba 2, porta 5020
3. Crie **3 fluxos de leitura periódica**, um para cada dispositivo, decodificando os valores principais.
4. Crie um **dashboard com 3 seções**:
   - Seção EM3P: tensões, potência, alarme
   - Seção Bomba 1: frequência, status, corrente
   - Seção Bomba 2: frequência, status, corrente
5. Cada seção tem um **gráfico histórico** das últimas 5 minutos.

> Use o conhecimento das **Práticas 3 e 6**. Não vamos repetir o passo-a-passo aqui — você já sabe.

**Verifique nos smartphones:** o contador de clientes em cada um deve subir.

**Compare os 3 dashboards:** deve haver consistência. Pequenas diferenças temporais são esperadas (cada laptop tem seu próprio polling timing).

---

### Etapa 5 — Lógica Coordenada de Proteção (45 min)

**Objetivo:** implementar a lógica:

> **"Se a corrente total do medidor exceder 25 A, ambos os VFDs devem reduzir frequência para 20 Hz como medida de proteção."**

**Decisão de design:** quem implementa essa lógica?

**Opção A — Centralizada:** apenas um aluno (Aluno 1) implementa a lógica. Os demais apenas monitoram.

**Opção B — Distribuída:** cada aluno implementa a mesma lógica. Race condition aceita (todos enviam o mesmo comando).

**Opção C — Coordenada:** Aluno 2 controla Bomba 1, Aluno 3 controla Bomba 2; ambos verificam o medidor (lido pelo Aluno 1) e agem em seus VFDs respectivos.

**Para esta prática, usem a Opção C** — é a mais didática e reflete melhor a arquitetura industrial real (cada controlador tem responsabilidade definida).

#### Implementação no Aluno 2 (Node-RED):

Adicione ao seu fluxo:

1. Um **inject** repetindo a cada 2s.
2. Um **Modbus Read** lendo a corrente do EM3P (FC04, addr 12, qty 6 — três correntes).
3. Um **function** que decodifica e verifica:

   ```javascript
   function wordsToFloat(h, l) {
       const buf = Buffer.alloc(4);
       buf.writeUInt16BE(h, 0);
       buf.writeUInt16BE(l, 2);
       return buf.readFloatBE(0);
   }
   const i_l1 = wordsToFloat(msg.payload[0], msg.payload[1]);
   const i_l2 = wordsToFloat(msg.payload[2], msg.payload[3]);
   const i_l3 = wordsToFloat(msg.payload[4], msg.payload[5]);
   const i_max = Math.max(i_l1, i_l2, i_l3);
   
   if (i_max > 25.0) {
       // Reduzir VFD1 para 20 Hz
       msg.payload = [0x41A0, 0x0000];  // 20.0 Hz em FLOAT32 ABCD
       msg.action = "PROTECT";
       return msg;
   }
   return null;  // não faz nada
   ```

4. Um **Modbus Write** para o **VFD1**: FC16, addr 101, qty 2.
5. Um **debug** para confirmar quando a proteção dispara.

**Aluno 3** faz o mesmo, mas escrevendo no VFD2.

#### Como testar:

**Manualmente, provoque uma sobre-corrente** no medidor:
- Tem um modo de simulação? **No simulador atual, a corrente é gerada automaticamente** com flutuação. Para forçar, **modifique o threshold** de over-current para abaixo do valor atual:
  - Escreva no Holding Register 111 do EM3P o valor `(0x41A0, 0x0000)` (= 20.0 A).
  - Imediatamente o alarm_status mudará e o valor de corrente será considerado alto.

Ou:
- **Use a função do simulador (se implementada)** de "boost de corrente" — verifique no app se tem essa opção.
- Alternativamente, **diminua o threshold para 5 A**, garantindo que a corrente já está acima.

**Observe:** ambos os VFDs devem reduzir frequência para 20 Hz.

✓ **Sucesso da Etapa 5:** vocês implementaram **automação coordenada multi-dispositivo**.

---

### Etapa 6 — Logging Sincronizado (30 min)

**Objetivo:** cada aluno gera seu próprio CSV com timestamps. Após a prática, comparem.

Cada aluno adiciona ao seu fluxo Node-RED um **file** node que escreve:

```
timestamp,em3p_v_l1,em3p_p_total,em3p_alarm,vfd1_freq,vfd1_status,vfd2_freq,vfd2_status
```

Polling: **a cada 5 segundos**.

Após **15 minutos** de operação (incluindo as etapas anteriores), cada aluno deve ter um CSV com ~180 linhas.

**Comparem os CSVs:** os valores devem ser **muito próximos** entre os 3 laptops, com pequenas variações temporais (diferença típica < 2 segundos entre eventos).

---

### Etapa 7 — Apresentação Coletiva (final)

A equipe junta tudo:

1. **Demo conjunta** (todos os 3 dashboards lado a lado).
2. **Demo de proteção:** alguém provoca over-current. Ambos VFDs reduzem.
3. **Análise dos CSVs:** mostrem em gráfico (matplotlib ou Excel) os 3 logs sincronizados na mesma timeline.
4. **Discussão pós-mortem:** o que deu errado durante a execução? Como vocês resolveram?

---

## 6. Critérios de Sucesso

A equipe completou a prática se:

- ✅ Os 3 smartphones estão simulando os 3 dispositivos corretamente.
- ✅ Os 3 laptops conseguem **simultaneamente** ler todos os 3 dispositivos via Python (Etapa 2).
- ✅ A equipe identificou e discutiu o problema de **race condition** (Etapa 3).
- ✅ Cada aluno construiu seu próprio dashboard Node-RED monitorando os 3 dispositivos (Etapa 4).
- ✅ A **lógica coordenada de proteção** funciona: over-current no medidor → ambos VFDs reduzem frequência (Etapa 5).
- ✅ Cada aluno gerou um **CSV de 15 minutos** (Etapa 6).
- ✅ A apresentação final foi coerente e demonstrou todos os conceitos (Etapa 7).

---

## 7. Discussão e Reflexão

A equipe responde **coletivamente**:

1. **Concorrência.** Vocês confirmaram que múltiplos clientes podem ler o mesmo servidor. Há limite? Em uma planta com **50 supervisórios** querendo ler o mesmo CLP, o que poderia dar errado?
2. **Coordenação de escrita.** Como vocês resolveriam o problema de race condition em uma planta real? Pesquisem o conceito de **"single point of write"** e como SCADAs profissionais lidam com isso.
3. **Latência.** Comparando os timestamps dos 3 CSVs, qual é a defasagem máxima entre os 3 laptops? Por que ela existe?
4. **Resiliência.** O que aconteceria se um dos smartphones perdesse Wi-Fi por 30 segundos no meio da operação? Como cada laptop reage? E a lógica de proteção?
5. **Arquitetura.** Para uma planta com 100 dispositivos, a arquitetura "todos lendo todos" não escala. Pesquisem e descrevam **três arquiteturas alternativas** (gateway intermediário, broker MQTT, banco compartilhado, etc.).
6. **Segurança.** Modbus TCP não tem autenticação. Em uma planta exposta à Internet, como vocês protegeriam essa comunicação?

---

## 8. Entregáveis Coletivos

Cada equipe submete um **relatório único de equipe**:

1. **Tabela** com os papéis assumidos por cada aluno e os IPs usados.
2. **Capturas de tela**:
   - Os 3 dashboards Node-RED lado a lado
   - O smartphone EM3P mostrando 3+ clientes conectados
   - Evidência da lógica de proteção em ação (antes e depois)
3. **Os 3 arquivos CSV** (um de cada aluno).
4. **Gráfico comparativo** (matplotlib ou Excel) mostrando, para uma variável (ex.: tensão L1 ou frequência VFD1), o valor logado por cada um dos 3 laptops na mesma timeline.
5. **Code dump** ou **export Node-RED** dos fluxos de cada aluno.
6. **Vídeo curto** (3–5 minutos) demonstrando:
   - Os 3 smartphones e os 3 laptops em operação
   - A lógica de proteção sendo acionada
7. **Respostas** às 6 perguntas da seção 7 (1–2 parágrafos cada).

---

## 9. Solução de Problemas Específicos

| Sintoma | Causa | Solução |
|---------|-------|---------|
| Smartphones em sub-redes diferentes | Wi-Fi com isolamento de clientes | Rede sem AP isolation; trocar de roteador |
| Pings funcionam mas Modbus não | Firewall do laptop | Permitir saída TCP 5020 |
| Cliente "trava" após algumas leituras | Sem timeout configurado | Adicione `timeout=2.0` ao ModbusTcpClient |
| Lógica de proteção não dispara | Threshold mal-definido | Verifique unidade (A vs hex) |
| 3 dashboards mostram valores divergentes | Timing de polling | Aumente o intervalo; aceite pequena defasagem |
| Comandos chegam fora de ordem | Race condition | Aplique a regra "single writer" |
| Smartphone trava no meio | Bateria/Memória | Reinicie o app, mantenha tela ligada |

---

## 10. Considerações Finais

Esta prática consolida tudo o que vocês aprenderam ao longo da disciplina:

- **Comunicação serial** (módulos 1–4) — embora aqui usamos TCP, o conceito de protocolo cliente-servidor é o mesmo.
- **Modbus** (módulos 5–9) — vocês escreveram clientes, decodificaram FLOAT32, construíram dashboards.
- **Boas práticas de software** — separação de responsabilidades (cada cliente tem seu papel), tratamento de erros, logging.
- **Pensamento sistêmico** — vocês não programaram um único equipamento, mas um **sistema distribuído**.

Em sua carreira profissional, quase sempre vocês trabalharão em **sistemas com múltiplos dispositivos**. As lições desta prática — race conditions, coordenação, latência, arquitetura — vão acompanhar vocês.

---

## 11. Critérios de Avaliação Detalhados

| Critério                                          | Peso |
|---------------------------------------------------|------|
| Funcionamento técnico (todas as etapas concluídas)| 35%  |
| Implementação correta dos 3 dashboards            | 15%  |
| Lógica coordenada de proteção operando           | 15%  |
| Qualidade dos CSVs e análise comparativa         | 10%  |
| Apresentação e demo                              | 15%  |
| Discussões e respostas às perguntas              | 10%  |

---

**Boa equipe! Lembrem-se: comunicação dentro do grupo é tão importante quanto a comunicação Modbus.**

— **Prof. Dênis Leite**
*Mekatronik — Advanced Engineering*
