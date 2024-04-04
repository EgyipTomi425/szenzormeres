from dateutil.parser import parse
from datetime import datetime
from datetime import timedelta
import pytz
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
from collections import defaultdict

NUM_SENSORS = 5 # Ha növeljük, több szenzort használhatunk szenzor1.csv, szenzor2.csv stb. elnevezés alapon
SENSOR_DATA = [[None, None] for _ in range(NUM_SENSORS)] # Annyira imádom, hogy nincsenek típusok, ez más nyelven sose történne meg
SENSOR_FILENAMES = ['szenzor{}.csv'.format(i + 1) for i in range(NUM_SENSORS)]
SENSOR_FILE_HANDLES = [open(filename, 'r') for filename in SENSOR_FILENAMES]
TIME = datetime(1970, 1, 1, 0, 0, 0, tzinfo=pytz.timezone('CET'))
TIME_PASSING = 10 # Másodperc
TIME_EPSILON = 3*TIME_PASSING
ROOM_WIDTH = 300
ROOM_HEIGHT = 100
ALL_DATA = []

plt.rcParams['toolbar'] = 'None'
fig, ax = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('Szenzorok mérési adatainak vizualizációja\n Idő: ' + TIME.strftime('%Y-%m-%d %H:%M:%S'), fontsize=16, color='white')
is_colorbar_created = [False, False]
date_format = DateFormatter('%Y.%m.%d\n%H:%M:%S', tz=pytz.timezone('CET'))

class SensorRowData:
    def __init__(self, timestamp, id, temperature, humidity, xpos, ypos):
        self.timestamp = parse(timestamp).astimezone(pytz.timezone('CET'))
        self.id = id
        self.temperature = temperature
        self.humidity = humidity
        self.xpos = xpos
        self.ypos = ypos

def read_next_sensor_data(sensor_index):
    file_handle = SENSOR_FILE_HANDLES[sensor_index]
    row = file_handle.readline()
    if row:
        parts = row.strip().split(',')
        timestamp, id, temperature, humidity, xpos, ypos = parts
        if(SENSOR_DATA[sensor_index][0] is None): # Ha lennének típusok, nem kéne ezzel szenvedni
            SENSOR_DATA[sensor_index][0] = SensorRowData(timestamp, id, temperature, humidity, xpos, ypos)
            SENSOR_DATA[sensor_index][1] = SensorRowData(timestamp, id, temperature, humidity, xpos, ypos)
        elif(SENSOR_DATA[sensor_index][0].timestamp > SENSOR_DATA[sensor_index][1].timestamp):
            SENSOR_DATA[sensor_index][1] = SensorRowData(timestamp, id, temperature, humidity, xpos, ypos)
        else:
            SENSOR_DATA[sensor_index][0] = SensorRowData(timestamp, id, temperature, humidity, xpos, ypos)
        print("Data for sensor {} read successfully.".format(sensor_index + 1))
        return True
    else:
        print("End of file reached for sensor {}.".format(sensor_index + 1))
        return False

def update_sensor_data_by_time():
    global TIME
    update_happened=False
    for i in range(len(SENSOR_DATA)):
        update_need=True
        for j in range(len(SENSOR_DATA[i])):
            if(SENSOR_DATA[i][j].timestamp>TIME):
                update_need=False
                break
        if(update_need):
            update_happened=read_next_sensor_data(i)
    if(update_happened):
        update_sensor_data_by_time()

def get_latest_data():
    global SENSOR_DATA
    global ROOM_WIDTH
    global ROOM_HEIGHT
    global TIME
    global TIME_EPSILON

    # Szenzor pozíciók inicializálása és legfrissebb adatok felhasználása
    sensor_positions = []
    latest_temperatures = []
    latest_humidities = []
    sensor_ids = []

    for i,sensor_data_row in enumerate(SENSOR_DATA):
        latest_data = None
        for data_point in sensor_data_row:
            time_difference = abs((data_point.timestamp - TIME).total_seconds())
            if time_difference <= TIME_EPSILON:
                if latest_data is None or data_point.timestamp > latest_data.timestamp:
                    latest_data = data_point
        if latest_data is not None:
            sensor_positions.append((int(latest_data.xpos), int(latest_data.ypos)))
            latest_temperatures.append(float(latest_data.temperature))
            latest_humidities.append(float(latest_data.humidity))
            sensor_ids.append(i+1)
    
    # Visszaadunk egy tuple-t, ami tartalmazza a négy listát
    return (sensor_positions, latest_temperatures, latest_humidities, sensor_ids, TIME)
    
def calculate_heatmap(data_tuple):
    sensor_positions, latest_temperatures, latest_humidities, sensor_ids, TIME = data_tuple

    Z_temperature = np.zeros((ROOM_HEIGHT, ROOM_WIDTH))
    Z_humidity = np.zeros((ROOM_HEIGHT, ROOM_WIDTH))

    for i in range(ROOM_HEIGHT):
        for j in range(ROOM_WIDTH):
            distances = np.linalg.norm(np.array(sensor_positions) - [j, i], axis=1)
            weights = 1 / (distances + 1e-6)
            Z_temperature[i, j] = np.sum(weights * np.array(latest_temperatures)) / np.sum(weights)
            Z_humidity[i, j] = np.sum(weights * np.array(latest_humidities)) / np.sum(weights)

    X, Y = np.meshgrid(np.linspace(0, ROOM_WIDTH, ROOM_WIDTH), np.linspace(0, ROOM_HEIGHT, ROOM_HEIGHT))

    # Visszaadjuk az X, Y koordinátákat, a hőmérsékleti és páratartalmi adatokat, a szenzor pozíciókat és az azonosítókat
    return X, Y, Z_temperature, Z_humidity, sensor_positions, sensor_ids, TIME
    
def plot_heatmap(data_tuple):
    global fig
    global ax
    X, Y, Z_temperature, Z_humidity, sensor_positions, sensor_ids, TIME = data_tuple
    fig.suptitle('Szenzorok mérési adatainak vizualizációja\n Idő: ' + TIME.strftime('%Y-%m-%d %H:%M:%S'), fontsize=16, color='white')
    fig.patch.set_facecolor('black')
    for a in ax.flat:
        a.set_facecolor('black')
    sensor_data_structure = defaultdict(lambda: {'times': [], 'temperatures': [], 'humidities': []})

    for data in ALL_DATA:
        sensor_positions, latest_temperatures, latest_humidities, sensor_ids, time = data
        for i, sensor_id in enumerate(sensor_ids):
            sensor_data_structure[sensor_id]['times'].append(time)
            sensor_data_structure[sensor_id]['temperatures'].append(latest_temperatures[i] if i < len(latest_temperatures) else None)
            sensor_data_structure[sensor_id]['humidities'].append(latest_humidities[i] if i < len(latest_humidities) else None)
    
    for axs in ax.flat:
        axs.clear()
    
    dx, dy = 3, 3 

    ax[0, 0].scatter([pos[0] for pos in sensor_positions], [pos[1] for pos in sensor_positions], color='black', marker='x')
    for pos, sensor_id in zip(sensor_positions, sensor_ids):
        ax[0, 0].text(pos[0] + dx, pos[1] + dy, str(sensor_id), color='black', fontsize=12, ha='left', va='bottom')
    cax1 = ax[0, 0].imshow(Z_temperature, extent=(0, ROOM_WIDTH, ROOM_HEIGHT, 0), origin='upper', cmap='jet', vmin=15, vmax=25)
    if not is_colorbar_created[0]:
        colorbar1 = plt.colorbar(cax1, ax=ax[0, 0])
        colorbar1.set_label('Hőmérséklet (°C)', color='white')
        colorbar1.ax.yaxis.set_tick_params(color='white')
        colorbar1.ax.yaxis.label.set_color('white')
        # Az összes tick címke színének beállítása fehérre
        for label in colorbar1.ax.get_yticklabels():
            label.set_color('white')
        is_colorbar_created[0] = True
    ax[0, 0].set_title('Hőmérsékleti térkép')
    ax[0, 0].set_xlabel('X pozíció')
    ax[0, 0].set_ylabel('Y pozíció')

    ax[1, 0].scatter([pos[0] for pos in sensor_positions], [pos[1] for pos in sensor_positions], color='black', marker='x')
    for pos, sensor_id in zip(sensor_positions, sensor_ids):
        ax[1, 0].text(pos[0] + dx, pos[1] + dy, str(sensor_id), color='black', fontsize=12, ha='left', va='bottom')
    cax2 = ax[1, 0].imshow(Z_humidity, extent=(0, ROOM_WIDTH, ROOM_HEIGHT, 0), origin='upper', cmap='jet_r', vmin=20, vmax=60)
    if not is_colorbar_created[1]:
        colorbar2 = plt.colorbar(cax2, ax=ax[1, 0])
        colorbar2.set_label('Páratartalom (%)', color='white')
        colorbar2.ax.yaxis.set_tick_params(color='white')
        colorbar2.ax.yaxis.label.set_color('white')
        for label in colorbar2.ax.get_yticklabels():
            label.set_color('white')
        is_colorbar_created[1] = True
    ax[1, 0].set_title('Páratartalom térkép')
    ax[1, 0].set_xlabel('X pozíció')
    ax[1, 0].set_ylabel('Y pozíció')
    
    global date_format
    
    for sensor_id, adat in sensor_data_structure.items():
        ax[0, 1].plot(adat['times'], adat['temperatures'], label=f'Szenzor {sensor_id}')
    ax[0, 1].set_title('Hőmérséklet változása időben')
    ax[0, 1].set_xlabel('Idő')
    ax[0, 1].set_ylabel('Hőmérséklet (°C)')
    ax[0, 1].legend(loc='lower left')
    ax[0, 1].xaxis.set_major_formatter(date_format) 

    for sensor_id, adat in sensor_data_structure.items():
        ax[1, 1].plot(adat['times'], adat['humidities'], label=f'Szenzor {sensor_id}')
    ax[1, 1].set_title('Páratartalom változása időben')
    ax[1, 1].set_xlabel('Idő')
    ax[1, 1].set_ylabel('Páratartalom (%)')
    ax[1, 1].legend(loc='lower left')
    ax[1, 1].xaxis.set_major_formatter(date_format)

    for a in ax.flat:
        a.xaxis.label.set_color('white')
        a.yaxis.label.set_color('white')
        a.title.set_color('white')
        for spine in a.spines.values():
            spine.set_edgecolor('white')
        a.tick_params(colors='white', which='both')
    
    plt.tight_layout()
    
    print("\n")
    for sensor_id, adat in sensor_data_structure.items():
        print(f"Szenzor ID: {sensor_id}")
        print("Időpontok:", [ido.strftime('%H:%M:%S') for ido in adat['times']])
        print("Hőmérsékletek:", adat['temperatures'])
        print("Páratartalmak:", adat['humidities'])
        print("\n")
    
    plt.pause(0.1)

def setup():
    # Szükség van kezdeti adatokra
    for i in range(NUM_SENSORS):
        read_next_sensor_data(i)

    global TIME
    global TIME_PASSING
    # Végigmegyünk a szenzor adatokon és megkeressük a legújabb dátumot
    for sensor_data in SENSOR_DATA:
        for sensor_row in sensor_data:
            if sensor_row is not None and sensor_row.timestamp > TIME:
                TIME = sensor_row.timestamp
    TIME += timedelta(seconds=(0 - TIME.second % TIME_PASSING))
    update_sensor_data_by_time()
    print("Starting TIME:", TIME)

def main():
    global TIME
    global TIME_PASSING
    global ALL_DATA
    TIME += timedelta(seconds=700)
    for i in range(10000):
        TIME += timedelta(seconds=TIME_PASSING)
        update_sensor_data_by_time()
        print("Actual TIME: ", TIME)
        ALL_DATA.append(get_latest_data())
        plot_heatmap(calculate_heatmap(ALL_DATA[-1]))

if __name__ == "__main__":
    for sensor_index in range(NUM_SENSORS):
        file_handle = SENSOR_FILE_HANDLES[sensor_index]
        row = file_handle.readline() # A fejlécek beolvasásának elkerülése
    print("Start")
    setup()
    main()
    for file_handle in SENSOR_FILE_HANDLES:
        file_handle.close()  # Fájlkezelők lezárása
