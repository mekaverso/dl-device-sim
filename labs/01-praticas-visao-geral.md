# Visão Geral das Práticas de Laboratório

> *"Cada prática a seguir é uma pequena jornada completa. Você pode fazê-las em qualquer ordem."*

## Sobre Este Material

Este guia organiza **10 práticas de laboratório autônomas**, projetadas para que o aluno desenvolva domínio prático de Modbus TCP usando os simuladores do nosso projeto:

- **MK-EM3P** — medidor de energia trifásico
- **MK-VFD7** — inversor de frequência (motor drive)

**Característica importante:** todas as práticas são **autocontidas e independentes**. Você pode realizar qualquer prática sem ter feito as anteriores. Cada uma inclui o contexto, a revisão dos conceitos necessários, instruções passo-a-passo e critérios de sucesso bem definidos.

---

## Arquitetura Comum

Em todas as práticas individuais, o cenário base é o mesmo:

```
   ┌─────────────────────────┐                  ┌─────────────────────┐
   │     Smartphone Android  │                  │       Laptop        │
   │                         │                  │                     │
   │   ModbusDeviceSIM       │                  │  Cliente Modbus     │
   │   (APK instalado)       │                  │  (varia por prática)│
   │                         │                  │                     │
   │   • Pode simular        │                  │  • EasyModbusTCP    │
   │     MK-EM3P              │◄────Wi-Fi───────►│  • Python pymodbus  │
   │     OU                  │                  │  • Node-RED         │
   │   • MK-VFD7              │                  │                     │
   │                         │                  │                     │
   │   Modbus TCP server     │                  │                     │
   │   Porta: 5020           │                  │                     │
   │   Unit ID: 1            │                  │                     │
   └─────────────────────────┘                  └─────────────────────┘
                       Mesma rede Wi-Fi
```

> **Por que porta 5020 e não 502?** A porta 502 (padrão Modbus TCP) é "privilegiada" em alguns sistemas Android, e nem sempre o app consegue se ligar a ela. **5020** funciona em todos os dispositivos testados. Configure seu cliente para porta 5020.

---

## Pré-requisitos Comuns a Todas as Práticas

Antes de iniciar **qualquer** das práticas:

1. **APK do ModbusDeviceSIM** instalado no smartphone Android.
2. Smartphone e laptop conectados à **mesma rede Wi-Fi**.
3. Smartphone com **bateria suficiente** (recomendado: > 50 %) e **tela mantida acesa** (configure "manter tela ligada" durante as práticas).
4. Firewall do Windows **permitindo tráfego TCP de saída** para a porta 5020.
5. Você sabe **identificar o IP do smartphone** (mostrado na tela do app após pressionar START).

### Verificação rápida da conectividade

Antes de começar qualquer prática:

```
   No PC, abra o terminal:
   ping <IP_DO_SMARTPHONE>
```

Se houver respostas, você está pronto. Se não, verifique a rede Wi-Fi antes de prosseguir.

---

## O Que é Obrigatório e O Que é Escolha

### Práticas com EasyModbusTCP — OBRIGATÓRIAS

Para cada dispositivo (MK-EM3P e MK-VFD7), a prática com **EasyModbusTCP é obrigatória**. Ela garante que você entendeu o protocolo Modbus TCP de forma direta, antes de automatizar qualquer coisa.

> EasyModbusTCP é uma ferramenta gráfica que permite enviar comandos Modbus manualmente, registro a registro. Usá-la primeiro é o equivalente a "ver os pacotes na mão" antes de escrever código.

### Práticas de Implementação — Python OU Node-RED (sua escolha)

Após a prática obrigatória com EasyModbusTCP, você vai implementar uma solução para cada dispositivo. Aqui, **você escolhe uma ferramenta: Python ou Node-RED**. Não é necessário fazer as duas.

| Escolha | Quando faz sentido |
|---------|-------------------|
| **Python** | Se você prefere código, quer praticar programação, ou vai implementar lógica mais complexa |
| **Node-RED** | Se você prefere programação visual, quer um dashboard rápido, ou está focado em integração |

> Dica do professor: escolha a ferramenta que você ainda **não domina**. O objetivo é aprender, não confirmar o que já sabe.

**Resumo do que cada aluno entrega:**

```
   Para o MK-EM3P:
      ✔ Prática 1 — EasyModbusTCP (obrigatória)
      ✔ Prática 2 — Python         ← escolha UMA
        Prática 3 — Node-RED       ←

   Para o MK-VFD7:
      ✔ Prática 4 — EasyModbusTCP (obrigatória)
      ✔ Prática 5 — Python         ← escolha UMA
        Prática 6 — Node-RED       ←

   Em grupo (todos participam de todas):
      ✔ Prática G1 + G2 + G3 + G4
```

---

## Catálogo das Práticas (10 ao todo: 6 individuais + 4 em grupo)

### Práticas Individuais — MK-EM3P (Medidor de Energia)

| # | Arquivo | Ferramenta | Obrigatoriedade |
|---|---------|------------|-----------------|
| 1 | [02-pratica-em3p-easymodbus.md](02-pratica-em3p-easymodbus.md) | EasyModbusTCP | **OBRIGATÓRIA** |
| 2 | [03-pratica-em3p-python.md](03-pratica-em3p-python.md) | Python + pymodbus | Escolha: Python **ou** Node-RED |
| 3 | [04-pratica-em3p-nodered.md](04-pratica-em3p-nodered.md) | Node-RED | Escolha: Python **ou** Node-RED |

### Práticas Individuais — MK-VFD7 (Inversor de Frequência)

| # | Arquivo | Ferramenta | Obrigatoriedade |
|---|---------|------------|-----------------|
| 4 | [05-pratica-vfd7-easymodbus.md](05-pratica-vfd7-easymodbus.md) | EasyModbusTCP | **OBRIGATÓRIA** |
| 5 | [06-pratica-vfd7-python.md](06-pratica-vfd7-python.md) | Python + pymodbus | Escolha: Python **ou** Node-RED |
| 6 | [07-pratica-vfd7-nodered.md](07-pratica-vfd7-nodered.md) | Node-RED | Escolha: Python **ou** Node-RED |

### Práticas em Grupo

| # | Arquivo | Configuração | Foco |
|---|---------|-------------|------|
| G1 | [08-pratica-grupo-1-3clientes-1vfd.md](08-pratica-grupo-1-3clientes-1vfd.md) | 3 alunos / 1 VFD | Operador + Supervisor + Manutenção (papéis) |
| G2 | [09-pratica-grupo-2-1cliente-3vfds.md](09-pratica-grupo-2-1cliente-3vfds.md) | 1 cliente / 3 VFDs | Orquestração centralizada (sequência, load sharing) |
| G3 | [10-pratica-grupo-3-3clientes-3vfds.md](10-pratica-grupo-3-3clientes-3vfds.md) | 3 alunos / 3 VFDs | Operação distribuída independente |
| G4 | [11-pratica-grupo-4-mini-planta.md](11-pratica-grupo-4-mini-planta.md) | 3 alunos / 2 VFDs + 1 medidor | Mini-planta integrada com interlock |

---

## Estrutura de Cada Prática

Todas as práticas seguem o mesmo formato:

```
   1. Contexto Industrial
      Por que essa prática faz sentido na vida real
   2. Conceitos Necessários
      Revisão concisa dos conceitos teóricos relevantes
   3. Material e Setup
      O que você precisa ter à mão
   4. Procedimento
      Passo-a-passo com comandos e códigos
   5. Critérios de Sucesso
      Como saber se você conseguiu
   6. Discussão e Reflexão
      Perguntas para fixar o aprendizado
   7. Entregáveis (para avaliação)
      O que ir no relatório
```

---

## O Que Você Vai Aprender (Síntese)

Ao final de **todas** as práticas, você terá:

- **Configurado** uma comunicação Modbus TCP de zero (rede + cliente + servidor).
- **Lido** medições e configurações de dispositivos industriais.
- **Escrito** parâmetros e comandos.
- **Decodificado** valores FLOAT32 a partir de registradores brutos.
- **Implementado** clientes em três tecnologias diferentes (ferramenta gráfica, código Python, fluxo Node-RED).
- **Construído** um dashboard com visibilidade em tempo real, gráficos históricos e capacidade de alterar parâmetros.
- **Coordenado** comunicação simultânea com múltiplos dispositivos.
- **Aplicado** boas práticas: tratamento de erros, reconexão, logs, segurança básica.

---

## Recomendação de Ordem (Opcional)

Embora as práticas sejam independentes, sugerimos a seguinte sequência para um aluno **que está aprendendo do zero**. As práticas de Python e Node-RED são alternativas — escolha uma para cada dispositivo:

```
   ① Prática 1 (EM3P + EasyModbusTCP)  ← OBRIGATÓRIA — protocolo na prática
   ② Prática 2 (EM3P + Python)         ← ESCOLHA UMA
      Prática 3 (EM3P + Node-RED)      ←

   ③ Prática 4 (VFD7 + EasyModbusTCP)  ← OBRIGATÓRIA — controle interativo
   ④ Prática 5 (VFD7 + Python)         ← ESCOLHA UMA
      Prática 6 (VFD7 + Node-RED)      ←

   ⑤ Prática Grupo 1 (3 clientes / 1 VFD)           ← papéis distintos
   ⑥ Prática Grupo 2 (1 cliente / 3 VFDs)           ← orquestração
   ⑦ Prática Grupo 3 (3 clientes / 3 VFDs)          ← operação distribuída
   ⑧ Prática Grupo 4 (3 clientes / 2 VFDs + 1 medidor) ← integração final
```

Você pode começar por qualquer prática se já tem familiaridade com partes do conteúdo — mas sempre faça o EasyModbusTCP antes de implementar em Python ou Node-RED para o mesmo dispositivo.

---

## Avaliação

Cada aluno entrega **4 práticas individuais**: EasyModbusTCP para o EM3P, EasyModbusTCP para o VFD7, e mais uma de implementação por dispositivo (Python ou Node-RED).

Cada **prática individual** vale **3 %** da nota total (4 × 3 % = 12 %).
Cada **prática em grupo** vale **3,25 %** (4 × 3,25 % = 13 %).
Total: **25 %** das avaliações de laboratório.

**Critérios por prática:**

- **40 %** — Critérios de sucesso técnicos atingidos
- **30 %** — Qualidade do relatório (clareza, capturas, organização)
- **20 %** — Análise das perguntas de discussão
- **10 %** — Boas práticas (organização do código, comentários, segurança)

---

## Boas Práticas para Todas as Práticas

1. **Documente conforme avança.** Não deixe o relatório para depois.
2. **Salve capturas de tela** dos resultados-chave.
3. **Comente seu código** mesmo nos scripts pequenos.
4. **Anote o que deu errado.** Documentar erros é tão importante quanto documentar sucessos.
5. **Versione com Git.** Mesmo para scripts pequenos, fazer commits ajuda a reconstruir seu raciocínio.
6. **Trabalhe em parceria.** Discutir problemas com colegas acelera o aprendizado.

---

## Solução de Problemas Genérica

| Sintoma | Onde investigar |
|---------|----------------|
| Smartphone e laptop não pingam | Mesma rede Wi-Fi? Firewall do roteador? |
| Ping OK mas Modbus não conecta | Porta 5020? App rodando? Firewall do laptop? |
| Conecta mas valores estranhos | Função code certa? FC04 para medições, FC03 para config |
| FLOAT32 lê valor errado | Ordem dos bytes (ABCD)? Endereço high/low certo? |
| VFD não responde aos comandos | Modo REMOTE ativado no app? |
| Tela do smartphone apaga | Configure "manter tela ligada" no Android |

---

**Próximo passo:** Escolha uma prática do catálogo acima e comece. Bom trabalho!
