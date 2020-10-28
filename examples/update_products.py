#!/usr/bin/env python3

# Example program for converting a Deutsche Post provided ppl_vXXX.csv file
# to JSON. See also the data package sub-directory.
#
# Example call:
#
#     $ update_products.py ppl_v450.csv inema/data/products.json \
#                                       inema/data/products-2020-01-01.json
#
#
# Note: PPL stands for Product Price List

import sys
import json
import csv

def main(csv_filename, json_filename, filename):
    with open(csv_filename, newline='', encoding='latin-1') as f \
            , open(json_filename) as g \
            , open(filename, 'w') as h:
        rows = csv.reader(f, delimiter=';')
        products = json.load(g)

        seen_ids = set()
        for row in rows:
            key, price = row[2], row[5].replace(',', '.')
            inter, weight, name =  row[3]=='1', row[21], row[4]
            seen_ids.add(row[2])
            if key in products:
                p = products[key]
                oprice, ointer = p['cost_price'], p['international']
                oweight, oname  = p['max_weight'], p['name']
                # row[5] vs. row[7] => total vs. base product price
                # row[4] vs. row[6] => complete vs. base product name
                c = False
                if price != oprice:
                    print(f'Price of {name} ({key}) changed: {oprice} -> {price} (from {row[0]})')
                    c = True
                    p['cost_price'] = price
                if inter != ointer:
                    print(f'Nationality of {name} ({key}) changed: {ointer} -> {inter} (from {row[0]})')
                    c = True
                    p['international'] = inter
                if weight != oweight:
                    print(f'Weight of {name} ({key}) changed: {oweight} -> {weight} (from {row[0]})')
                    c = True
                    p['max_weight'] = weight
                # The names returned by the ProdWS differ from the ones included in the PPL ...
                # if name != oname:
                #    print(f'Name of {name} ({key}) changed: {oname} -> {name} (from {row[0]})')
                #    c = True
                if c:
                    print('*'*75)
            else:
                products[key] = {
                        "cost_price": price,
                        "international": inter,
                        "max_weight": weight,
                        "name": name
                        }
                print(f'NEW Product {row[4]} ({row[2]}) - from {row[0]}!')
                print('*'*75)

        remove_ids = set()
        for k in products:
            if k not in seen_ids:
                p = products[k]
                print(f'Product {p["name"]} ({k}) was deleted!')
                remove_ids.add(k)
        for k in remove_ids:
            products.pop(k)

        json.dump(products, h, sort_keys=True, indent=4, ensure_ascii=False)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
