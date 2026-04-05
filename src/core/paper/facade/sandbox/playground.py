#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Paper Trading Playground — Sandbox Interativo

Demonstra o PaperOrchestrator rodando com workers,
simulação de mercado e métricas em tempo real.

Uso:
    python -m src.core.paper.facade.sandbox.playground

Comandos disponíveis:
    status   → Ver estado do portfolio
    buy      → Comprar ativo
    sell     → Vender ativo
    quote    → Ver cotação
    tick     → Executar 1 tick manual
    run      → Rodar N ticks automáticos
    reset    → Resetar portfolio
    help     → Mostrar comandos
    quit     → Sair
"""

import asyncio
import json
import logging
import random
import sys
from decimal import Decimal
from typing import Optional

from ...domain.currency import Currency

logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s",
)

# ── Cores ANSI ────────────────────────────────────────────────────────────────

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
RESET = "\033[0m"


# ── Simulador de Mercado Inline ───────────────────────────────────────────────

class MercadoPlayground:
    """Simulador de mercado leve para o playground."""

    PRECOS_INICIAIS = {
        "BTC-USD": Decimal("88000"),
        "ETH-USD": Decimal("3200"),
        "SOL-USD": Decimal("185"),
        "PETR4.SA": Decimal("38.50"),
        "VALE3.SA": Decimal("62.30"),
    }

    def __init__(self):
        self.precos: dict[str, Decimal] = dict(self.PRECOS_INICIAIS)
        self.historico: dict[str, list[Decimal]] = {
            k: [v] for k, v in self.precos.items()
        }

    def tick(self) -> None:
        """Atualiza preços com movimento aleatório."""
        for ticker, preco in self.precos.items():
            volatilidade = Decimal("0.02") if "-USD" in ticker else Decimal("0.01")
            cambio = Decimal(str(random.gauss(0, float(volatilidade))))
            novo = preco * (1 + cambio)
            novo = novo.quantize(Decimal("0.01"))
            self.precos[ticker] = max(novo, Decimal("0.01"))
            self.historico[ticker].append(self.precos[ticker])
            # Manter últimas 100 amostras
            if len(self.historico[ticker]) > 100:
                self.historico[ticker] = self.historico[ticker][-100:]

    def preco(self, ticker: str) -> Decimal:
        return self.precos.get(ticker.upper(), Decimal("0"))

    def moeda(self, ticker: str) -> Currency:
        return Currency.USD if "-USD" in ticker.upper() else Currency.BRL


# ── Estado do Playground ──────────────────────────────────────────────────────

class PlaygroundState:
    """Estado do playground em memória."""

    def __init__(self, saldo_inicial: Decimal = Decimal("100000")):
        self.saldo_inicial = saldo_inicial
        self.saldo = saldo_inicial
        self.posicoes: dict[str, dict] = {}
        self.ordens: list[dict] = []
        self.operacoes_abertas: list[dict] = []
        self.tick_count = 0

    def comprar(self, ticker: str, qty: Decimal, preco: Decimal, moeda: Currency) -> str:
        valor = qty * preco
        if self.saldo < valor:
            return f"{RED}Saldo insuficiente: {self.saldo:.2f} < {valor:.2f}{RESET}"

        self.saldo -= valor

        if ticker not in self.posicoes:
            self.posicoes[ticker] = {
                "qty": qty,
                "preco_medio": preco,
                "moeda": moeda,
                "custo_total": valor,
            }
        else:
            pos = self.posicoes[ticker]
            nova_qty = pos["qty"] + qty
            pos["preco_medio"] = (pos["custo_total"] + valor) / nova_qty
            pos["custo_total"] += valor
            pos["qty"] = nova_qty

        ordem_id = f"ORD-{len(self.ordens)+1:04d}"
        self.ordens.append({
            "id": ordem_id,
            "ticker": ticker,
            "lado": "COMPRA",
            "qty": qty,
            "preco": preco,
            "valor": valor,
            "moeda": moeda,
            "tick": self.tick_count,
        })

        return f"{GREEN}COMPRA {qty} {ticker} @ {preco} = {valor:.2f} {moeda.value}{RESET}"

    def vender(self, ticker: str, qty: Decimal, preco: Decimal) -> str:
        if ticker not in self.posicoes:
            return f"{RED}Sem posição em {ticker}{RESET}"

        pos = self.posicoes[ticker]
        if pos["qty"] < qty:
            return f"{RED}Quantidade insuficiente: {pos['qty']} < {qty}{RESET}"

        valor = qty * preco
        custo = qty * pos["preco_medio"]
        pnl = valor - custo
        pnl_pct = (pnl / custo * 100) if custo > 0 else Decimal("0")

        self.saldo += valor
        pos["qty"] -= qty
        pos["custo_total"] -= custo

        if pos["qty"] <= 0:
            del self.posicoes[ticker]

        ordem_id = f"ORD-{len(self.ordens)+1:04d}"
        self.ordens.append({
            "id": ordem_id,
            "ticker": ticker,
            "lado": "VENDA",
            "qty": qty,
            "preco": preco,
            "valor": valor,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "moeda": pos.get("moeda", Currency.BRL),
            "tick": self.tick_count,
        })

        cor = GREEN if pnl >= 0 else RED
        return f"{cor}VENDA {qty} {ticker} @ {preco} | PnL: {pnl:+.2f} ({pnl_pct:+.1f}%){RESET}"

    def patrimonio(self, mercado: MercadoPlayground) -> dict:
        valor_posicoes = Decimal("0")
        for ticker, pos in self.posicoes.items():
            preco_atual = mercado.preco(ticker)
            valor_posicoes += pos["qty"] * preco_atual

        total = self.saldo + valor_posicoes
        pnl = total - self.saldo_inicial
        pnl_pct = (pnl / self.saldo_inicial * 100) if self.saldo_inicial > 0 else Decimal("0")

        return {
            "saldo": self.saldo,
            "valor_posicoes": valor_posicoes,
            "patrimonio": total,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
        }


# ── Display Helpers ───────────────────────────────────────────────────────────

def print_header():
    print(f"\n{BOLD}{CYAN}{'='*60}")
    print(f"  PAPER TRADING PLAYGROUND — Sandbox Interativo")
    print(f"{'='*60}{RESET}")
    print(f"\n{DIM}Saldo inicial: R$ 100,000.00 | Digite 'help' para comandos{RESET}\n")


def print_status(state: PlaygroundState, mercado: MercadoPlayground):
    pat = state.patrimonio(mercado)
    cor_pnl = GREEN if pat["pnl"] >= 0 else RED

    print(f"\n{BOLD}{'─'*50}")
    print(f"  PORTFOLIO STATUS (tick #{state.tick_count})")
    print(f"{'─'*50}{RESET}")
    print(f"  Saldo:          R$ {pat['saldo']:>12,.2f}")
    print(f"  Posições:       R$ {pat['valor_posicoes']:>12,.2f}")
    print(f"  {BOLD}Patrimônio:      R$ {pat['patrimonio']:>12,.2f}{RESET}")
    print(f"  PnL:          {cor_pnl}R$ {pat['pnl']:>+12,.2f} ({pat['pnl_pct']:>+.1f}%){RESET}")

    if state.posicoes:
        print(f"\n{BOLD}  POSIÇÕES:{RESET}")
        for ticker, pos in state.posicoes.items():
            preco_atual = mercado.preco(ticker)
            valor = pos["qty"] * preco_atual
            pnl = (preco_atual - pos["preco_medio"]) * pos["qty"]
            pnl_pct = ((preco_atual / pos["preco_medio"]) - 1) * 100
            cor = GREEN if pnl >= 0 else RED
            moeda = pos.get("moeda", Currency.BRL)
            print(
                f"    {ticker:<12} {pos['qty']:>8} @ {pos['preco_medio']:>10} "
                f"→ {preco_atual:>10} | {cor}{pnl:>+10,.2f} ({pnl_pct:>+5.1f}%){RESET}"
            )

    print(f"\n{BOLD}  COTAÇÕES:{RESET}")
    for ticker, preco in mercado.precos.items():
        hist = mercado.historico[ticker]
        if len(hist) >= 2:
            cambio = ((preco / hist[-2]) - 1) * 100
            seta = f"{GREEN}▲{RESET}" if cambio > 0 else f"{RED}▼{RESET}" if cambio < 0 else "─"
        else:
            cambio = Decimal("0")
            seta = "─"
        moeda = "$" if "-USD" in ticker else "R$"
        print(f"    {ticker:<12} {moeda}{preco:>10,.2f} {seta} {float(cambio):>+5.1f}%")

    print(f"{DIM}{'─'*50}{RESET}\n")


def print_help():
    print(f"""
{BOLD}COMANDOS:{RESET}
  {CYAN}status{RESET}          Estado do portfolio e cotações
  {CYAN}buy <ticker> <qtd>{RESET}   Comprar ativo (ex: buy BTC-USD 0.1)
  {CYAN}sell <ticker> <qtd>{RESET}  Vender ativo (ex: sell BTC-USD 0.05)
  {CYAN}quote <ticker>{RESET}       Ver cotação específica
  {CYAN}tick{RESET}             Executar 1 tick de mercado
  {CYAN}run <n>{RESET}          Rodar N ticks automáticos (default: 10)
  {CYAN}auto{RESET}             Rodar em loop contínuo (Ctrl+C para parar)
  {CYAN}orders{RESET}           Ver histórico de ordens
  {CYAN}reset{RESET}            Resetar portfolio
  {CYAN}help{RESET}             Mostrar este help
  {CYAN}quit{RESET}             Sair
""")


# ── Loop Principal ────────────────────────────────────────────────────────────

async def main():
    mercado = MercadoPlayground()
    state = PlaygroundState()
    print_header()
    print_status(state, mercado)

    loop = asyncio.get_event_loop()

    while True:
        try:
            cmd = await loop.run_in_executor(None, lambda: input(f"{BOLD}{CYAN}playground>{RESET} ").strip())
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}Até logo!{RESET}")
            break

        if not cmd:
            continue

        parts = cmd.split()
        action = parts[0].lower()

        if action == "quit" or action == "exit" or action == "q":
            print(f"{DIM}Até logo!{RESET}")
            break

        elif action == "help" or action == "h" or action == "?":
            print_help()

        elif action == "status" or action == "s":
            print_status(state, mercado)

        elif action == "tick" or action == "t":
            mercado.tick()
            state.tick_count += 1
            print(f"{DIM}Tick #{state.tick_count} executado{RESET}")
            print_status(state, mercado)

        elif action == "run" or action == "r":
            n = int(parts[1]) if len(parts) > 1 else 10
            print(f"{DIM}Rodando {n} ticks...{RESET}")
            for i in range(n):
                mercado.tick()
                state.tick_count += 1
            print(f"{GREEN}✓ {n} ticks executados (#{state.tick_count}){RESET}")
            print_status(state, mercado)

        elif action == "auto" or action == "a":
            interval = float(parts[1]) if len(parts) > 1 else 1.0
            print(f"{DIM}Auto mode: 1 tick a cada {interval}s (Ctrl+C para parar){RESET}")
            try:
                while True:
                    await asyncio.sleep(interval)
                    mercado.tick()
                    state.tick_count += 1
                    pat = state.patrimonio(mercado)
                    cor = GREEN if pat["pnl"] >= 0 else RED
                    print(
                        f"  tick #{state.tick_count:>4} | "
                        f"Patrimônio: R$ {pat['patrimonio']:>12,.2f} | "
                        f"PnL: {cor}R$ {pat['pnl']:>+10,.2f}{RESET}"
                    )
            except KeyboardInterrupt:
                print(f"\n{DIM}Auto mode parado{RESET}")
                print_status(state, mercado)

        elif action == "buy" or action == "b":
            if len(parts) < 3:
                print(f"{RED}Uso: buy <ticker> <quantidade>{RESET}")
                continue
            ticker = parts[1].upper()
            try:
                qty = Decimal(parts[2])
            except Exception:
                print(f"{RED}Quantidade inválida: {parts[2]}{RESET}")
                continue
            preco = mercado.preco(ticker)
            if preco == 0:
                print(f"{RED}Ticker não encontrado: {ticker}{RESET}")
                continue
            moeda = mercado.moeda(ticker)
            result = state.comprar(ticker, qty, preco, moeda)
            print(result)

        elif action == "sell" or action == "v":
            if len(parts) < 3:
                print(f"{RED}Uso: sell <ticker> <quantidade>{RESET}")
                continue
            ticker = parts[1].upper()
            try:
                qty = Decimal(parts[2])
            except Exception:
                print(f"{RED}Quantidade inválida: {parts[2]}{RESET}")
                continue
            preco = mercado.preco(ticker)
            if preco == 0:
                print(f"{RED}Ticker não encontrado: {ticker}{RESET}")
                continue
            result = state.vender(ticker, qty, preco)
            print(result)

        elif action == "quote" or action == "c":
            if len(parts) < 2:
                for t, p in mercado.precos.items():
                    moeda = "$" if "-USD" in t else "R$"
                    print(f"  {t:<12} {moeda}{p:>10,.2f}")
            else:
                ticker = parts[1].upper()
                preco = mercado.preco(ticker)
                if preco == 0:
                    print(f"{RED}Ticker não encontrado: {ticker}{RESET}")
                else:
                    moeda = "$" if "-USD" in ticker else "R$"
                    print(f"  {ticker}: {moeda}{preco:,.2f}")

        elif action == "orders" or action == "o":
            if not state.ordens:
                print(f"{DIM}Nenhuma ordem executada{RESET}")
            else:
                print(f"\n{BOLD}  HISTÓRICO DE ORDENS:{RESET}")
                for o in state.ordens[-20:]:  # Últimas 20
                    cor = GREEN if o["lado"] == "COMPRA" else MAGENTA
                    pnl_str = ""
                    if "pnl" in o:
                        pcor = GREEN if o["pnl"] >= 0 else RED
                        pnl_str = f" | {pcor}{o['pnl']:>+8,.2f}{RESET}"
                    print(
                        f"    {cor}{o['id']}{RESET} {o['lado']:<6} "
                        f"{o['qty']:>8} {o['ticker']:<12} @ {o['preco']:>10} "
                        f"= {o['valor']:>12,.2f}{pnl_str}"
                    )

        elif action == "reset":
            state.__init__()
            mercado.__init__()
            print(f"{YELLOW}Portfolio resetado! Saldo: R$ 100,000.00{RESET}")

        else:
            print(f"{RED}Comando desconhecido: {action}. Digite 'help'.{RESET}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{DIM}Playground encerrado.{RESET}")
        sys.exit(0)
