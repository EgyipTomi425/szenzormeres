import csv
import sys

def transform_csv(input_filename, xpos, ypos):
    output_filename = input_filename.split('.')[0] + '_transformed.csv'

    with open(input_filename, 'r') as infile, open(output_filename, 'w', newline='') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        # Az új fejléc sor írása
        writer.writerow(['Time', 'ID', 'Temperature', 'Humidity', 'xpos', 'ypos'])

	# Az első sort beolvasása, de nem írjuk ki
        next(reader)

        # Az adatok átírása és új oszlopok hozzáadása
        for row in reader:
            # Csak az első négy oszlopot tartjuk meg és átnevezzük
            time, entry_id, temperature, humidity = row[:4]
            writer.writerow([time, entry_id, temperature, humidity, xpos, ypos])
        print("Mentve: " + output_filename)

# Bemeneti paraméterek feldolgozása
if len(sys.argv) != 4:
    print("Usage: python csvclean.py <input_filename> <xpos> <ypos>")
    sys.exit(1)

input_filename = sys.argv[1]
xpos = sys.argv[2]
ypos = sys.argv[3]

# Átalakítás
transform_csv(input_filename, xpos, ypos)
