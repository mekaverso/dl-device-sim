# Prática 1 — MK-EM3P com EasyModbusTCP

> *"Sua primeira conversa real com um medidor de energia industrial."*

## 1. Contexto Industrial

Medidores de energia trifásicos como o **Schneider PM5xxx**, **Carlo Gavazzi EM340** ou **WEG MMW03** são utilizados em painéis elétricos para **monitorar consumo, qualidade de energia e identificar problemas**. Esses medidores expõem dezenas de variáveis (tensões por fase, correntes, potências ativa/reativa/aparente, fator de potência, energia acumulada) através de **Modbus TCP**.

Nesta prática, você irá:

- Conectar-se a um **medidor de energia simulado** (MK-EM3P) usando uma ferramenta de teste gráfica.
- Ler todas as medições principais.
- Modificar parâmetros de configuração (relação TC, thresholds de alarme).
- Provocar uma condição de alarme e observá-la.

Esta é a forma mais comum de **diagnosticar problemas de comunicação** em uma planta: o engenheiro abre uma ferramenta de teste, conecta-se ao IP do equipamento e verifica diretamente os registradores.

---

## 2. Conceitos Necessários

### 2.1 Modbus TCP em uma frase

Protocolo cliente-servidor sobre TCP/IP. **Cliente** (master) envia requisições, **servidor** (slave) responde. Porta padrão **502** (mas usaremos **5020** por compatibilidade com Android).

### 2.2 Function Codes que você usará

| FC   | Operação                              | Usa para               |
|------|---------------------------------------|------------------------|
| 04   | Read Input Registers                  | Ler medições (V, I, P, etc.) |
| 03   | Read Holding Registers                | Ler configurações      |
| 06   | Write Single Register                 | Alterar config UINT16  |
| 16   | Write Multiple Registers (FC10 hex)   | Alterar config FLOAT32 |

### 2.3 FLOAT32 em Modbus

Valores como tensão (220,5 V) e corrente (15,2 A) ocupam **2 registradores consecutivos** (32 bits). O simulador usa ordem **ABCD (big-endian)**:

```
   Reg N   = high word (bits 31-16)
   Reg N+1 = low word  (bits 15-0)
   Float = combinar como IEEE 754
```

### 2.4 Mapa de Registradores do MK-EM3P

**Medições (FC04 — Input Registers):**

| Endereço | Variável         | Tipo    | Unidade |
|----------|------------------|---------|---------|
| 0–1      | Voltage L1-N     | FLOAT32 | V       |
| 2–3      | Voltage L2-N     | FLOAT32 | V       |
| 4–5      | Voltage L3-N     | FLOAT32 | V       |
| 12–13    | Current L1       | FLOAT32 | A       |
| 14–15    | Current L2       | FLOAT32 | A       |
| 16–17    | Current L3       | FLOAT32 | A       |
| 26–27    | Active Power Total | FLOAT32 | kW    |
| 50–51    | Power Factor Total | FLOAT32 | —     |
| 52–53    | Frequency        | FLOAT32 | Hz      |
| 90       | Alarm Status     | UINT16  | bitmask |
| 91       | Device Status    | UINT16  | bitmask |

**Configuração (FC03 — Holding Registers):**

| Endereço | Variável               | Tipo    | Default |
|----------|------------------------|---------|---------|
| 100      | CT Primary             | UINT16  | 100 A   |
| 102      | VT Primary             | UINT16  | 220 V   |
| 107–108  | Over-Voltage Threshold | FLOAT32 | 253 V   |
| 109–110  | Under-Voltage Threshold| FLOAT32 | 198 V   |
| 111–112  | Over-Current Threshold | FLOAT32 | 30 A    |
| 117      | Alarm Enable Mask      | UINT16  | 0x001F  |

---

## 3. Material Necessário

- 1 **smartphone Android** com **ModbusDeviceSIM** instalado
- 1 **laptop Windows/Linux/macOS** com **EasyModbusTCP** instalado
- Conexão **Wi-Fi** que aceite ambos os dispositivos na mesma rede

### 3.1 Onde baixar EasyModbusTCP

[https://sourceforge.net/projects/easymodbustcp/](https://sourceforge.net/projects/easymodbustcp/)

Baixe o componente **EasyModbusTcp Master Tester** — é uma aplicação Windows standalone, sem instalação.

---

## 4. Setup Inicial

### 4.1 No smartphone

1. Abra o **ModbusDeviceSIM**.
2. No card **Device Type**, toque em **MK-EM3P** (deve estar selecionado em azul).
3. Toque no botão verde **START**.
4. O status muda para **RUNNING** em verde.
5. Anote o endereço exibido — exemplo: `192.168.0.105:5020`.
6. **Configure o smartphone para não desligar a tela:** Configurações → Display → Time-out → "Nunca" (ou ative o "manter tela ligada" no aplicativo).

### 4.2 No laptop

1. Verifique conectividade abrindo um terminal e executando:
   ```
   ping 192.168.0.105
   ```
   (substitua pelo IP do seu smartphone)
2. Se não houver resposta, verifique a rede Wi-Fi antes de prosseguir.
3. Abra o **EasyModbusTCP Master Tester**.

---

## 5. Procedimento

### Etapa 1 — Estabelecer Conexão

1. Na interface do EasyModbusTCP, localize os campos de conexão (geralmente no topo).
2. Preencha:
   - **IP Address:** o IP do smartphone (ex.: `192.168.0.105`)
   - **Port:** `5020`
   - **Unit Identifier:** `1`
3. Clique em **Connect**.
4. **Verifique no smartphone:** o contador **Clients** deve subir para **1**.

> ❌ **Se não conectar:** verifique IP, porta, firewall. **Não prossiga** até resolver.

---

### Etapa 2 — Ler Tensões e Correntes

1. No EasyModbusTCP, vá para a aba/área **Read Input Registers (FC04)**.
2. Configure:
   - **Start Address:** `0`
   - **Number of Inputs:** `18` *(lê do endereço 0 ao 17 = tensões e correntes)*
3. Clique em **Read**.
4. O EasyModbusTCP exibirá 18 valores brutos de 16 bits.
5. **Identifique** os pares de registradores e decodifique manualmente o primeiro float:
   - Reg 0 + Reg 1 = Voltage L1-N
   - Use uma calculadora online: [https://www.h-schmidt.net/FloatConverter/IEEE754.html](https://www.h-schmidt.net/FloatConverter/IEEE754.html)
   - Concatene os dois hex (high primeiro): ex.: `0x4360 0x0000` → `0x43600000` → **224.0**

> 💡 **Dica:** o EasyModbusTCP pode exibir floats automaticamente se você selecionar "Float (ABCD)" no formato de exibição (se disponível na sua versão).

---

### Etapa 3 — Ler Potência e Frequência

Configure uma nova leitura FC04:
- **Start Address:** `26`
- **Number of Inputs:** `28` *(até o endereço 53, cobrindo potência, fator de potência, frequência)*

Identifique e decodifique:

| Registradores | Variável            |
|---------------|---------------------|
| 26–27         | Active Power Total  |
| 50–51         | Power Factor Total  |
| 52–53         | Frequency           |

**Pergunta de verificação:** a frequência lida está próxima de **60.00 Hz** (ou 50, dependendo da configuração regional)?

---

### Etapa 4 — Ler Configurações

Agora mude para **FC03 (Read Holding Registers)**:
- **Start Address:** `100`
- **Number of Inputs:** `20`

Você verá os valores de configuração:

| Reg | Variável               | Valor padrão esperado |
|-----|------------------------|------------------------|
| 100 | CT Primary             | 100 (UINT16)           |
| 102 | VT Primary             | 220                    |
| 107–108 | Over-Voltage Threshold | 0x4382 0x0000 (= 260 V?) |

Verifique se os valores fazem sentido conforme a documentação do dispositivo.

---

### Etapa 5 — Escrever Configuração (UINT16)

Vá para a função **Write Single Register (FC06)**:
- **Register Address:** `100`
- **Value:** `200`

Clique em **Write**. Em seguida, releia o registrador 100 com FC03. Deve agora mostrar **200**.

✓ **Você acabou de mudar a relação do TC** (transformador de corrente) de 100 A para 200 A. Em um equipamento real, isso significaria que o medidor agora está calibrado para um TC de 200/5 A.

---

### Etapa 6 — Escrever um FLOAT32

Tarefa: mudar **Over-Voltage Threshold** (endereço 107) de 253 V para **245 V**.

**Passo 6.1 — Converter 245.0 para IEEE 754:**

- 245.0 em hex IEEE 754 = `0x43750000`
- High word = `0x4375` = **17269** (decimal)
- Low word = `0x0000` = **0**

**Passo 6.2 — Escrever com FC16 (Write Multiple Registers):**

- **Start Address:** `107`
- **Number of Registers:** `2`
- **Values:** `17269, 0`

Clique em **Write**.

**Passo 6.3 — Verificar:**

Releia FC03 a partir do endereço 107, 2 registradores. Deve mostrar `17269, 0`. ✓

---

### Etapa 7 — Provocar uma Condição de Alarme

Vamos forçar o medidor a entrar em alarme de sobre-tensão:

1. Reduza o threshold de sobre-tensão para abaixo da tensão atual (~220 V). Por exemplo, escreva **200.0 V** no endereço 107:
   - 200.0 em hex IEEE 754 = `0x43480000`
   - High word = `0x4348` = **17224**
   - Low word = `0` 
2. Use FC16 conforme antes.
3. Aguarde **alguns segundos** para o engine de simulação processar.
4. Leia o **Alarm Status** (registrador 90, FC04):
   - Configure: Start Address = `90`, Inputs = `1`, function code FC04.
   - O bit 0 (mask `0x0001`) deve estar ligado = **sobre-tensão ativa**.
5. **Confirme no smartphone:** o LED **OV** (Over-Voltage) no painel do app deve estar aceso em vermelho.

---

### Etapa 8 — Limpar o Alarme

1. Restaure o threshold para 253 V (`0x437D0000`):
   - High = `0x437D` = **17277**
   - Low = `0`
2. Reescreva o registrador 107 com FC16.
3. Aguarde e releia o registrador 90 — o bit 0 deve estar zerado.
4. O LED **OV** no app apaga.

---

## 6. Critérios de Sucesso

Você completou esta prática se conseguiu:

- ✅ Conectar EasyModbusTCP ao smartphone com sucesso (Clients = 1 no app).
- ✅ Ler as **3 tensões de fase** (L1, L2, L3) e decodificá-las em volts.
- ✅ Ler a **potência total** e a **frequência**.
- ✅ Modificar o **CT Primary** com FC06 e ler de volta o novo valor.
- ✅ Modificar um **threshold FLOAT32** com FC16 e ler de volta corretamente.
- ✅ Provocar e limpar uma **condição de alarme**, confirmando a mudança no bit de alarme e visualmente no app.

---

## 7. Discussão e Reflexão

Responda no seu relatório:

1. **Conceitual.** Por que ler a tensão exige **2 registradores** mas ler o CT Primary exige apenas **1**?
2. **Análise.** Capture (screenshot) os 18 valores brutos lidos na Etapa 2 e calcule manualmente a média das três tensões de fase. Compare com o valor lido no registrador "Avg Voltage L-N" (endereço 78, FC04). São iguais?
3. **Diagnóstico.** Se, na Etapa 5, ao ler de volta o CT Primary, você visse o valor `0xC800` (em vez de 200), o que isso significaria? Esse seria um problema do equipamento ou do cliente?
4. **Aplicação.** Em uma planta real, qual seria a consequência prática de configurar erroneamente o **CT Primary** em um medidor de energia? Pense em como isso afeta as medições de corrente e potência.
5. **Reflexão.** A ferramenta EasyModbusTCP é adequada para qual tipo de uso na vida industrial? Em que situações você **não** a usaria?

---

## 8. Entregáveis para Avaliação

Submeta um relatório PDF contendo:

1. **Capturas de tela** da ferramenta EasyModbusTCP mostrando:
   - Conexão estabelecida (Clients = 1)
   - Leitura das medições (Etapas 2 e 3)
   - Leitura de configuração (Etapa 4)
   - Escrita bem-sucedida (Etapa 5)
   - Estado de alarme ativo (Etapa 7)
2. **Tabela de valores brutos** lidos e seus equivalentes decodificados (mínimo 5 variáveis).
3. **Cálculo manual** mostrando como você decodificou um FLOAT32 a partir dos 2 registradores brutos.
4. **Respostas** às 5 perguntas da seção 7.

---

## 9. Solução de Problemas Específicos

| Sintoma | Causa provável | Solução |
|---------|---------------|---------|
| "Connection refused" | App não está RUNNING | Pressione START no smartphone |
| Conecta mas timeout em leitura | Porta errada (502 vs 5020) | Use porta **5020** |
| Lê valores absurdos para tensão | Função code errada (FC03 vs FC04) | Medições → **FC04** |
| FLOAT32 lê valor estranho | Ordem dos bytes (CDAB?) | Confirme ordem **ABCD** |
| Write retorna erro | Endereço read-only | Apenas regs 100+ são writáveis |
| Tela do app fica preta | Android sleep | Configure tela "sempre ligada" |

---

## 10. Próximos Passos

Após dominar esta prática:

- **[Prática 2 — EM3P com Python](03-pratica-em3p-python.md)**: automatize o que você fez manualmente.
- **[Prática 3 — EM3P com Node-RED](04-pratica-em3p-nodered.md)**: construa um dashboard visual.
- **[Prática 4 — VFD7 com EasyModbusTCP](05-pratica-vfd7-easymodbus.md)**: controle um inversor de frequência.

---

**Bom trabalho!**
