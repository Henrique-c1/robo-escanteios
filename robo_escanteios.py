import requests
import time

BOT_TOKEN = "7933494449:AAH5zueavo8TwS_oXRfmlevmfLlSs3T1LaE"
CHAT_ID = "-4755659481"
API_KEY = "f3abffe120cc661c6ea05e8cb4d3f8b1"

HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"

def enviar_sinal_telegram(mensagem):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': mensagem.encode('utf-8', 'ignore').decode('utf-8')
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Erro ao enviar mensagem para o Telegram:", str(e))

def coletar_jogos_ativos():
    url = f"{BASE_URL}/fixtures?live=all"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            jogos = data.get('response', [])
            lista_jogos = []

            for jogo in jogos:
                fixture_id = jogo['fixture']['id']
                home = jogo['teams']['home']['name']
                away = jogo['teams']['away']['name']
                minuto = jogo['fixture']['status']['elapsed']

                lista_jogos.append({
                    'id': fixture_id,
                    'home': home,
                    'away': away,
                    'minute': minuto
                })

            return lista_jogos
        else:
            print("Erro ao acessar API-Football: Status", response.status_code)
            return []
    except Exception as e:
        print("Erro na requisição:", str(e))
        return []

def coletar_estatisticas_jogo(fixture_id):
    url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json().get('response', [])
            stats = {}

            for equipe in data:
                for item in equipe['statistics']:
                    nome = item['type']
                    valor = item['value'] if isinstance(item['value'], int) else 0
                    if nome not in stats:
                        stats[nome] = valor
                    else:
                        stats[nome] += valor

            return stats
        else:
            print("Erro nas estatísticas: Status", response.status_code)
            return None
    except Exception as e:
        print("Erro nas estatísticas:", str(e))
        return None

def analisar_e_decidir(jogo, estatisticas):
    minuto = jogo['minute']
    if minuto is None:
        return

    primeiro_tempo = 33 <= minuto <= 45
    segundo_tempo = 78 <= minuto <= 90

    if not (primeiro_tempo or segundo_tempo):
        return

    ataques_perigosos = estatisticas.get('Dangerous Attacks', 0)
    finalizacoes = estatisticas.get('Total Shots', 0)
    posse = estatisticas.get('Ball Possession', 0)
    escanteios = estatisticas.get('Corner Kicks', 0)

    if (ataques_perigosos >= 10 and
        finalizacoes >= 2 and
        posse >= 50):

        linha_estimativa = escanteios + 2 if escanteios < 8 else escanteios + 1

        mensagem = (
            f"[SINAL DETECTADO]\n"
            f"{jogo['home']} x {jogo['away']} - Minuto {minuto}'\n"
            f"Mercado: Over Escanteios (pressão ofensiva detectada)\n"
            f"Linha estimada: {linha_estimativa}.5 (com base no volume atual de escanteios)"
        )
        enviar_sinal_telegram(mensagem)

if __name__ == "__main__":
    while True:
        print("Buscando jogos ativos...")
        jogos_ativos = coletar_jogos_ativos()

        if jogos_ativos:
            for jogo in jogos_ativos:
                print(f"Analisando {jogo['home']} x {jogo['away']} - Minuto {jogo['minute']}")
                estatisticas = coletar_estatisticas_jogo(jogo['id'])
                if estatisticas:
                    analisar_e_decidir(jogo, estatisticas)
        else:
            print("Nenhum jogo ativo encontrado.")

        print("[OK] Loop ativo - aguardando próximo ciclo\n")
        time.sleep(60)
