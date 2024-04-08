import csv
import os
import math

# Beállítható változók
input_file = 'data_from_2024-03-25_till_2024-04-02.csv'
output_folder = './'  # Jelenlegi könyvtár, de beállítható

# Szenzor pozíciók beállításai
room_width = 300
room_height = 100
margin = 10  # Széleken hagyott hely

# Ellenőrizzük, hogy létezik-e a kimeneti könyvtár, ha nem, hozzuk létre
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Előkészítjük a szenzor fájlok kezelését és a pozíciókat
sensor_files = {}
sensor_writers = {}
sensor_ids = {}
sensor_positions = {}
unique_sensors = set()

# Először összegyűjtjük az összes egyedi szenzort
with open(input_file, mode='r', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    for row in reader:
        if row['process-status'].lower() != 'warning':
            unique_sensors.add(int(row['diversen-id']))

num_sensors = len(unique_sensors)
rows = cols = int(math.ceil(math.sqrt(num_sensors)))  # Egyenletes elosztás sorokban és oszlopokban

x_spacing = (room_width - 2 * margin) // (cols - 1 if cols > 1 else 1)
y_spacing = (room_height - 2 * margin) // (rows - 1 if rows > 1 else 1)

# Pozíciók kiszámítása
for index, sensor_id in enumerate(sorted(unique_sensors)):
    row = index // cols
    col = index % cols
    xpos = margin + col * x_spacing
    ypos = margin + row * y_spacing
    sensor_positions[sensor_id] = (xpos, ypos)

# Adatok írása a fájlokba
try:
    with open(input_file, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            if row['process-status'].lower() != 'warning':
                diversen_id = int(row['diversen-id'])
                if diversen_id in sensor_positions:
                    xpos, ypos = sensor_positions[diversen_id]
                    if diversen_id not in sensor_files:
                        sensor_files[diversen_id] = open(f'{output_folder}szenzor{diversen_id}.csv', mode='w', newline='', encoding='utf-8')
                        sensor_writers[diversen_id] = csv.writer(sensor_files[diversen_id])
                        sensor_writers[diversen_id].writerow(['Time', 'ID', 'Temperature', 'Humidity', 'xpos', 'ypos'])
                        sensor_ids[diversen_id] = 1

                    sensor_writers[diversen_id].writerow([row['ttn-received-at'], sensor_ids[diversen_id], row['temperature'], row['humidity'], xpos, ypos])
                    sensor_ids[diversen_id] += 1
            else:
                print("\nÉrvénytelen sor:",row)
finally:
    for f in sensor_files.values():
        f.close()

print("Data cleaning and distribution completed.")
