from machine import * #lib utilisation module ESP32
from hcsr04 import HCSR04 #lib capteur HCSR-04
import time, utime, wificonnect
import tft_config, st7789 #lib tft pour affichage sur ttgo t-display
import picoweb #affichage de la page web, ajouter utemplate, pgk_ressources et ulogging aux lib
import vga1_bold_16x32, vga2_16x16 # font



# ------------------------------------------ TANK SIZE -------------------------------------------------------------------------
# Enter the size of your own tank

# définition taille de la cuve
hauteur_max_eau = 1.60   # max level of liquid in meter  / hauteur d'eau maxi dans la cuve en m
position_capteur = 0.22  # distance between sensor and max level in meter / distance entre le capteur et le niveau maxi de la cuve en m
dimension_cuve_X = 1.10  # X size of the tank / taille de la cuve en X en m
dimension_cuve_Y = 5.68  # Y size of the tank / taille de la cuve en Y en m

# -------------------------------------------------------------------------------------------------------------------------------


# definition pin module
led_bleu = Pin(27, Pin.OUT, 0)
led_verte1 = Pin(26, Pin.OUT, 0)
led_verte2 = Pin(25, Pin.OUT, 0)
led_jaune1 = Pin(33, Pin.OUT, 0)
led_jaune2 = Pin(32, Pin.OUT, 0)
led_rouge = Pin(12, Pin.OUT, 0)
buzzer = Pin(15, Pin.OUT, 0)

# definition du display
tft = tft_config.config()
tft.init()

# definition variables:
surface_cuve = dimension_cuve_X * dimension_cuve_Y
volume_max_cuve = round(surface_cuve * hauteur_max_eau, 2)
volume_disponible = 0.00
timer = Timer(0)

# connexion au wifi
ipaddress = wificonnect.connectSTA(ssid='PAROLA_WIFI', password='LilieLuluKelia25')
print(ipaddress)


def leds_init():
    led_bleu.off()
    led_verte1.off()
    led_verte2.off()
    led_jaune1.off()
    led_jaune2.off()
    led_rouge.off()


def calcul_volume():
    data = []
    try:
        for i in range(1, 10):
            mesure = HCSR04(trigger_pin=22, echo_pin=21)
            distance = mesure.distance_cm() / 100
            time.sleep(0.3)
            data.append(distance)
            print(distance)
        distance_moyenne = sum(data)/len(data)
        volume_disponible = round(((hauteur_max_eau + position_capteur) * surface_cuve) - (distance_moyenne * surface_cuve), 2)
        print("Distance: ", distance_moyenne, " m\nVolume disponible: ", volume_disponible, " m3")
        return volume_disponible
    except:
        print('erreur prise de mesure')
        error()
        pass
        
 
def affichage():
    global volume_disponible
    nouveau_volume = calcul_volume()
    if nouveau_volume != volume_disponible:
        leds_init()
        volume_disponible = nouveau_volume
        if volume_max_cuve > volume_disponible >= 0.1*volume_max_cuve:
            if volume_disponible >= 0.9*volume_max_cuve:
                led_bleu.on()
            elif 0.8*volume_max_cuve <= volume_disponible < 0.9*volume_max_cuve:
                led_verte1.on()
            elif 0.6*volume_max_cuve <= volume_disponible < 0.8*volume_max_cuve:
                led_verte2.on()
            elif 0.4*volume_max_cuve <= volume_disponible < 0.6*volume_max_cuve:
                led_jaune1.on()
            elif 0.2*volume_max_cuve <= volume_disponible < 0.4*volume_max_cuve:
                led_jaune2.on()
            elif 0.1*volume_max_cuve <= volume_disponible < 0.2*volume_max_cuve:
                led_rouge.on()
            tft.fill(st7789.BLACK)
            tft.text(vga1_bold_16x32, "NIVEAU CUVE", 35, 15, st7789.CYAN)
            tft.text(vga2_16x16, "Capacite: 10m3", 6, 60, st7789.YELLOW)
            tft.text(vga2_16x16, "Reste: ", 15, 95, st7789.GREEN)
            tft.text(vga2_16x16, str(volume_disponible), 120, 95, st7789.GREEN)
            tft.text(vga2_16x16, "m3", 190, 95, st7789.GREEN)
        elif 0 <= volume_disponible < 0.1*volume_max_cuve:
            buzzer.on()
            led_rouge.value(not led_rouge.value())
            tft.fill(st7789.YELLOW)
            tft.text(vga1_bold_16x32, "Cuve quasi", 40, tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.YELLOW)
            tft.text(vga1_bold_16x32, "vide : < 1 m3", 20, (tft.height() // 3)*2 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.YELLOW)
        else:
            error()
    else:
        pass


def error():
    tft.fill(st7789.BLACK)
    tft.text(vga1_bold_16x32, "MESURE", 80, tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.BLACK)
    text = "ERRONEE"
    length=len(text)
    tft.text(vga1_bold_16x32, text, tft.width() // 2 - length // 2 * vga1_bold_16x32.WIDTH, 2 * tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.BLACK)
    

def handleInterrupt(timer):
    affichage()
    
    
tft.init()
tft.fill(st7789.GREEN)
tft.text(vga1_bold_16x32, "BIENVENUE", 45, tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.MAGENTA, st7789.GREEN)
tft.text(vga1_bold_16x32, "Attendez", 50, 2*(tft.height() // 3) - vga1_bold_16x32.HEIGHT//2, st7789.MAGENTA, st7789.GREEN)


# ---- Routing Picoweb ------------------------------------ 
app = picoweb.WebApp(__name__)
@app.route("/")
def index(req, resp):
    yield from picoweb.start_response(resp)
    yield from app.sendfile(resp, '/web/index.html')


@app.route("/get_volume")
def get_volume(req, resp):
    global volume_disponible
    yield from picoweb.jsonify(resp, {'volume': volume_disponible})


@app.route("/style.css")
def css(req, resp):
    print("Send style.css")
    yield from picoweb.start_response(resp)
    yield from app.sendfile(resp, '/web/style.css')
    

timer.init(period=6000, mode=Timer.PERIODIC, callback=handleInterrupt)
app.run(debug=True, host = ipaddress, port = 80)