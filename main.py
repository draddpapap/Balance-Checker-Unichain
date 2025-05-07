from web3 import Web3
from rich import print
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv
import os
import questionary  # Заменяем inquirer на questionary

# Загрузка переменных окружения
load_dotenv('rpc_url.env')
load_dotenv('wallets.env')

# Данные о токенах
TOKEN_DATA = {
    'USDC': {
        'address': '0x078D782b760474a361dDA0AF3839290b0EF57AD6',
        'decimals': 6
    },
    'USDT': {
        'address': '0x588ce4f028d8e7b53b687865d6a67b3a54c75518',
        'decimals': 6
    }
}


def get_web3_connection():
    """Подключаемся к RPC провайдеру"""
    rpc_urls = [
        os.getenv("INFURA_UNICHAIN_RPC"),
        os.getenv("ONFINALITY_UNICHAIN_RPC")
    ]

    for rpc_url in rpc_urls:
        try:
            web3 = Web3(Web3.HTTPProvider(rpc_url))
            if web3.is_connected():
                print(f"[green]✅ Connected to RPC: {rpc_url[:30]}...[/green]")
                return web3
        except Exception as e:
            print(f"[yellow]⚠️ Connection error with {rpc_url[:30]}...: {str(e)}[/yellow]")
            continue

    print(Panel.fit("[red]❌ Could not connect to any RPC provider[/red]",
                    title="Connection Error",
                    border_style="red"))
    return None


def get_token_balance(web3, wallet_address, token_address):
    """Получаем баланс токена"""
    try:
        # Минимальный ABI для функции balanceOf
        abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'
        contract = web3.eth.contract(address=token_address, abi=abi)
        return contract.functions.balanceOf(wallet_address).call()
    except Exception as e:
        print(f"[yellow]⚠️ Token balance error: {str(e)}[/yellow]")
        return 0


def check_wallet_balances():
    """Проверяем балансы кошельков"""
    web3 = get_web3_connection()
    if not web3:
        return False

    # Получаем все кошельки
    wallets = {k: v.strip() for k, v in os.environ.items()
               if k.startswith('WALLET_') and v.strip()}

    if not wallets:
        print(Panel.fit("[red]❌ No valid wallets found in wallets.env[/red]",
                        title="Wallet Error",
                        border_style="red"))
        return False

    table = Table(title="💰 [bold]Unichain Wallet Balances[/]",
                  show_lines=True,
                  header_style="bold magenta")
    table.add_column("Wallet", style="cyan", no_wrap=True)
    table.add_column("Address", style="magenta", no_wrap=True)
    table.add_column("ETH", style="green", justify="right")
    table.add_column("USDC", style="blue", justify="right")
    table.add_column("USDT", style="yellow", justify="right")

    for wallet_name, address in wallets.items():
        try:
            # Очищаем адрес от возможных пробелов и переводов строк
            address = address.strip()

            if not address.startswith('0x') or len(address) != 42:
                print(f"[yellow]⚠️ Invalid address format in {wallet_name}: {address}[/yellow]")
                continue

            checksum_address = Web3.to_checksum_address(address.lower())

            # Получаем балансы
            eth_balance = web3.eth.get_balance(checksum_address)
            usdc_balance = get_token_balance(web3, checksum_address, TOKEN_DATA['USDC']['address'])
            usdt_balance = get_token_balance(web3, checksum_address, TOKEN_DATA['USDT']['address'])

            # Форматируем значения
            eth_balance = web3.from_wei(eth_balance, 'ether')
            usdc_balance = usdc_balance / (10 ** TOKEN_DATA['USDC']['decimals'])
            usdt_balance = usdt_balance / (10 ** TOKEN_DATA['USDT']['decimals'])

            table.add_row(
                wallet_name,
                checksum_address,
                f"{eth_balance:.6f}",
                f"{usdc_balance:.2f}",
                f"{usdt_balance:.2f}"
            )

        except Exception as e:
            print(f"[red]❌ Error processing {wallet_name} ({address}): {str(e)}[/red]")
            continue

    print()
    print(table)
    print()
    return True


def get_module():
    """
    Функция для выбора действия в главном меню (используем questionary вместо inquirer)
    """
    result = questionary.select(
        "Choose module",
        choices=[
            "1) Посмотреть assets для каждого кошелька в сети Unichain",
            "2) Выход"
        ],
        qmark="⚙️ ",
        pointer="✅ "
    ).ask()  # Используем .ask() вместо .execute()
    return result


def main():

    """
    Главная функция, управляющая выбором действия и выполнением.
    """
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')  # Очистка консоли
        print(Panel.fit("[bold magenta]🦄 Unichain Wallet Balance Checker[/]",
                        border_style="bright_magenta"))

        module = get_module()

        if module == "1) Посмотреть assets для каждого кошелька в сети Unichain":
            print("\n" + "=" * 50 + "\n")
            check_wallet_balances()
            input("\nНажмите Enter чтобы продолжить...")
        elif module == "2) Выход":
            print(Panel.fit("[bold green]👋 До свидания![/]",
                            title="Exit",
                            border_style="green"))
            break


if __name__ == "__main__":
    main()