# Syrixin — Intelligent System Monitor

Syrixin é um monitor de sistema inteligente que acompanha em tempo real os recursos do seu computador — CPU, memória, disco e bateria — com logs automáticos e alertas integrados. Projetado para evoluir com inteligência artificial, permitindo análise preditiva e detecção de anomalias.

---

## Funcionalidades

- Monitoramento de uso de CPU
- Monitoramento de memória RAM
- Monitoramento de espaço em disco
- Monitoramento de bateria e status de carregamento
- Registro automático em log com timestamp
- Alertas automáticos para situações críticas

---

## Estrutura do Projeto

```
Syrixin/
├── main.py               # Ponto de entrada
├── monitor/
│   ├── cpu.py            # Coleta de CPU
│   ├── memory.py         # Coleta de RAM
│   ├── disk.py           # Coleta de disco
│   └── battery.py        # Coleta de bateria
├── models/
│   └── system_info.py    # Modelo de dados do sistema
├── utils/
│   └── formatter.py      # Formatação de saída
└── logs/
    ├── logger.py         # Configuração de logging
    └── monitor.log       # Arquivo de log gerado
```

---

## Como usar

1. Instale as dependências:

```bash
pip install psutil
```

2. Execute o monitor:

```bash
python main.py
```

---

## Roadmap

- [x] Coleta de métricas do sistema
- [x] Sistema de logging com alertas
- [ ] Integração com IA para análise preditiva
- [ ] Detecção de anomalias em tempo real
- [ ] Dashboard visual
- [ ] Notificações inteligentes

---

## Tecnologias

- Python 3.x
- psutil
- logging (stdlib)

---

*Syrixin — watching your system, so you don't have to.*
