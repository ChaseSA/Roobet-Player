import requests, threading, json
from fake_useragent import UserAgent
import random, string, time
from colorama import Fore, init

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

lock = threading.Lock()
init(convert=True, autoreset=True)
AMOUNT_WON = 0

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

class roobet:

    global AMOUNT_WON

    def __init__(self, capkey="", proxy=""):
        self.capkey = capkey
        self.session = requests_retry_session()
        self.session.proxies.update({"https":"https://"+proxy})
        self.ua = UserAgent().google

        self.username = ('').join(random.choices(string.ascii_letters + string.digits, k=13))
        self.password = ('').join(random.choices(string.ascii_letters + string.digits, k=13))
        self.round = 0
        self.promo = '' #Enter promo code here

        self.identifier = str(random.randint(1,999999))

    def set_title(self, args):
        ctypes.windll.kernel32.SetConsoleTitleW(args)

    def safe_print(self, args):
        lock.acquire()
        print(args)
        lock.release()

    def solver(self, site_key, url):
        captcha_id = requests.post("http://2captcha.com/in.php?key={}&method=userrecaptcha&googlekey={}&pageurl={}".format(self.capkey, site_key, url)).text.split('|')[1]
        recaptcha_answer = requests.get("http://2captcha.com/res.php?key={}&action=get&id={}".format(self.capkey, captcha_id)).text
        while 'CAPCHA_NOT_READY' in recaptcha_answer:
            time.sleep(5)
            recaptcha_answer = requests.get("http://2captcha.com/res.php?key={}&action=get&id={}".format(self.capkey, captcha_id)).text
        try:
            recaptcha_answer = recaptcha_answer.split('|')[1]
        except:
            self.solver(site_key, url)
        return recaptcha_answer

    def register(self):
        self.safe_print('Starting registration')
        get_cookies = self.session.options('https://api.roobet.com/auth/signup', headers={'Accept':'*/*', 'User-Agent':self.ua})
        if 'POST' in get_cookies.text:
            captcha_answer = self.solver('6LdG97YUAAAAAHMcbX2hlyxQiHsWu5bY8_tU-2Y_', 'https://roobet.com/')
            headers = {"Connection": "keep-alive","Accept": "application/json, text/plain, */*","User-Agent": self.ua,"Content-Type": "application/json;charset=UTF-8","Origin": "https://roobet.com","Sec-Fetch-Site": "same-site","Sec-Fetch-Mode": "cors","Sec-Fetch-Dest": "empty","Referer": "https://roobet.com/?modal=auth&tab=register","Accept-Encoding": "gzip, deflate, br","Accept-Language": "en-US,en;q=0.9",}
            data = {'username':self.username, 'password':self.password, 'recaptcha':captcha_answer, 'passwordConfirm':self.password}
            register = self.session.post('https://api.roobet.com/auth/signup', json=data, headers=headers)
            if register.json()['token'] == None:
                self.safe_print('Created %s:%s' % (self.username, self.password))
                self.redeem_promo()
            else:
                self.safe_print('Error creating account')

    def redeem_promo(self):
        self.safe_print('Redeeming promo: %s' % (self.promo))
        captcha = self.solver('6LcyLZQUAAAAALOaIzlr4pTcnRRKEQn-d6sQIFUx', 'https://roobet.com/?modal=cashier&tab=free&expanded=promo')
        data = {'code':self.promo, 'recaptcha':captcha}
        redeem = self.session.post('https://api.roobet.com/promo/redeemCode', json=data, headers={'User-Agent':self.ua})
        try:
            if redeem.json()['success'] == True:
                self.safe_print('%sRedeemed promo code: %s' % (Fore.YELLOW, self.promo))
                self.start_game()
            else:
                self.safe_print('Error redeeming promo code')
                return
        except:
            self.safe_print('Error redeeming promo code')
            return

    def start_game(self):
        url = 'https://api.roobet.com/towers/gameboardLayout?amount=0.02&difficulty=hard'
        headers = {'User-Agent':self.ua}
        board = self.session.get(url, headers=headers)
        get_cookies = self.session.options('https://api.roobet.com/towers/start', headers=headers)
        if 'POST' in get_cookies.text:
            #self.safe_print('Starting game...')
            data = {'clientSeed':'ylVKPSBWNilmNH11', 'amount':0.02, 'difficulty':'hard'}
            start = self.session.post('https://api.roobet.com/towers/start', json=data, headers=headers)
            if 'GameId' in start.text:
                game_id = start.json()['activeGameId']
                self.safe_print('Started game %s' % (game_id))
                self.session.options('https://api.roobet.com/towers/selectCard', headers=headers)
                possible = [0, 1, 2]
                card = random.choice(possible)
                data = {'selectedCard':card, 'activeGameId':game_id}
                pick_card = self.session.post('https://api.roobet.com/towers/selectCard', json=data, headers=headers)
                #self.safe_print(pick_card.text)
                try:
                    if pick_card.json()['bet']['won'] == False:
                        self.safe_print('%sStatus: Lost game %s with card %d || %s' % (Fore.RED, game_id, card, self.identifier))
                except:
                    try:
                        if pick_card.json()['result'] == 'fruit':
                            self.round += 1
                            self.safe_print('%sStatus: Won round %d with card %d || %s' % (Fore.GREEN, self.round, card, self.identifier))
                            self.replay_round(game_id)
                    except Exception as e:
                        self.safe_print('Error starting game')
                        self.safe_print(e)
        else:
            self.safe_print('Error starting game')

    def replay_round(self, game_id):
        headers = {'User-Agent':self.ua}
        possible = [0, 1, 2]
        card = random.choice(possible)
        data = {'selectedCard':card, 'activeGameId':game_id}
        pick_card = self.session.post('https://api.roobet.com/towers/selectCard', json=data, headers=headers)
        try:
            if pick_card.json()['bet']['won'] == False:
                self.safe_print('%sStatus: Lost game %s with card %d || %s' % (Fore.RED, game_id, card, self.identifier))
        except:
            try:
                if pick_card.json()['result'] == 'fruit':
                    self.round += 1
                    self.safe_print('%sStatus: Won round %d with card %d || %s' % (Fore.GREEN, self.round, card, self.identifier))
                    if self.round != 6:
                        self.replay_round(game_id)
                    else:
                        get_cookies = self.session.options('https://api.roobet.com/towers/cashout', headers=headers)
                        cash = {'activeGameId':game_id}
                        cashout = self.session.post('https://api.roobet.com/towers/cashout', json=cash, headers=headers)
                        
                        lock.acquire()
                        with open('won.txt', 'a', encoding='utf-8', errors='ignore') as f:
                            f.write('%s:%s\n' % (self.username, self.password))
                        lock.release()

                        self.safe_print('%sWON $13 ON %s || %s' % (Fore.GREEN, game_id, self.identifier))
                        AMOUNT_WON += 13
                        self.set_title('Roobet | Won $%d' % (AMOUNT_WON))
            except Exception as e:
                self.safe_print('Error starting game')
                self.safe_print(e)

if __name__ == "__main__":

    def load_data():
        config = open('config.json', 'r')
        data = json.load(config)
        captcha_key = data['captcha-key']
        proxies = [line.replace('\n','') for line in open('proxies.txt', 'r', encoding='utf-8', errors='ignore').readlines()]
        return captcha_key, proxies

    captcha_key, proxies = load_data()

    def start_thread():
        roo = roobet(capkey=captcha_key, proxy=random.choice(proxies))
        roo.register()

    while True:
        if threading.active_count() <= 30:
            threading.Thread(target=start_thread, args=(),).start()