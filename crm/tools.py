import os
import json
import boto3
import random
import pandas as pd

from datetime import datetime, timedelta
from flask import request, session
from boto3.dynamodb.conditions import Key, Attr


class Secret:
    with open(".secret", "r", encoding="utf-8") as s:
        data = json.load(s)
    url = data["url"]
    parameter = data["parameter"]
    secret_key = data["secret_key"]
    access_key_id = data["access_key_id"]
    secret_access_key = data["secret_access_key"]
    region_name = data["region_name"]


class Tools:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb',
                                       aws_access_key_id=Secret.access_key_id,
                                       aws_secret_access_key=Secret.secret_access_key,
                                       region_name=Secret.region_name)
        self.table_users = self.dynamodb.Table('kullanicilar')
        self.table_product = self.dynamodb.Table('urunler')
        self.table_stock = self.dynamodb.Table('stok')
        self.table_log = self.dynamodb.Table('log')
        self.table_input = self.dynamodb.Table('inputs')

    @staticmethod
    def generate_password():
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!?"
        new_password = ""
        for x in range(0, 12):
            password_char = random.choice(chars)
            new_password += password_char
        return new_password

    @staticmethod
    def auth():
        auth_ = request.args.get('parametre', None)
        if auth_ == 'aZ3Fg629Hj871Kl453Mn087Pq265Rs941Tu738Vw124Xy670Za356Bc092Df814E':
            return True
        else:
            return False

    def insert(self, username_, password, service_, add, stock, log_, type_):
        input_ = {
            "username": username_,
            "password": password,
            "servis": service_,
            "email": "",
            "ekle": add,
            "stok": stock,
            "log": log_,
            "type": type_
        }
        self.table_users.put_item(Item=input_)

    def users_number(self):
        response = self.table_users.scan()
        return len(response['Items'])

    @staticmethod
    def created_product_number():
        with open("created_product_number", "r") as f:
            number = f.read()
        return int(number)

    def set_created_product_number(self):
        number = self.created_product_number()
        number += 1
        with open("created_product_number", "w") as f:
            f.write(str(number))

    def insert_products(self, product_name, contents):
        input_ = {
            "Urun_Ismi": product_name,
            "Icindekiler": contents,
        }
        self.table_product.put_item(Item=input_)

    def get_email(self, username_):
        credential = self.query_authority(username_)
        if not credential:
            return None
        credential = dict(credential[0])
        email = credential['email']
        return email

    def get_password(self, username_):
        credential = self.query_authority(username_)
        if not credential:
            return None
        credential = dict(credential[0])
        password = credential['password']
        return password

    def change(self, item, username_, value):
        if item == "email":
            self.table_users.update_item(
                Key={
                    'username': username_
                },
                UpdateExpression='SET email = :email',
                ExpressionAttributeValues={
                    ':email': value
                }
            )
        else:
            self.table_users.update_item(
                Key={
                    'username': username_
                },
                UpdateExpression='SET password = :password',
                ExpressionAttributeValues={
                    ':password': value
                }
            )

    def query_authority(self, username_):
        filtering_exp = Key('username').eq(username_)
        response = self.table_users.query(KeyConditionExpression=filtering_exp)
        items = response["Items"]
        return items

    def query_product(self, product_name):
        filtering_exp = Key('Urun_Ismi').eq(product_name)
        response = self.table_product.query(KeyConditionExpression=filtering_exp)
        items = response["Items"]
        return items

    def get_param(self, username_):
        credential = self.query_authority(username_)
        if not credential:
            return None
        credential = dict(credential[0])
        service_ = int(credential['servis'])
        add = int(credential["ekle"])
        stock = int(credential['stok'])
        log_ = int(credential['log'])
        user_type_ = credential['type']
        return service_, add, stock, log_, user_type_

    @staticmethod
    def recent_activity(type_):
        username_ = str(session.get('user_name', None))
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        now = str(datetime.today()).split(" ")[0]
        data = {"username": username_, "type": type_, "date": now, "time": current_time}
        with open("recent_activity.json", "r+") as newfile:
            newfile_list = newfile.read().split("\n")
            if len(newfile_list) == 5:
                with open("recent_activity.json", "w") as file:
                    for i in range(1, 5, 1):
                        if i == 4:
                            file.write(newfile_list[i])
                        else:
                            file.write(newfile_list[i] + "\n")
            with open("recent_activity.json", "a") as file:
                file.write("\n")
                json.dump(data, file, default=str)

    @staticmethod
    def get_recent_activity():
        usernames = []
        types = []
        dates = []
        times = []
        with open('recent_activity.json') as f:
            for line in f:
                obj = json.loads(line)
                usernames.append(obj["username"])
                types.append(obj["type"])
                dates.append(obj["date"])
                times.append(obj["time"])
        return usernames, types, dates, times

    @staticmethod
    def number_of_products():
        with open('products.json', "r") as file:
            file = list(json.load(file).keys())
            return len(file)

    def open_new_stock(self, special_code, unit, amount=0.0, explanation=""):
        input_ = {
            "Ozel_Kod": special_code,
            "Miktar": str(amount),
            "Birim": unit,
            "Aciklama": explanation
        }
        self.table_stock.put_item(Item=input_)

    def query_stock(self, special_code):
        filtering_exp = Key('Ozel_Kod').eq(special_code)
        response = self.table_stock.query(KeyConditionExpression=filtering_exp)
        items = response["Items"]
        return items

    def get_amount(self, special_code):
        stock_info = self.query_stock(special_code)
        if not stock_info:
            amount = 0.0
        else:
            stock_info = dict(stock_info[0])
            amount = stock_info['Miktar']
        return amount

    def update_stock(self, special_code, amount, explanation):
        self.table_stock.update_item(
            Key={
                'Ozel_Kod': special_code
            },
            UpdateExpression='SET Miktar = :Miktar, Aciklama = :aciklama',
            ExpressionAttributeValues={
                ':Miktar': str(amount),
                ':aciklama': str(explanation)
            }
        )

    def get_stock(self):
        response = self.table_stock.scan()
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = self.table_stock.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
        return data

    def stock_log(self, company, product_code, special_code, amount,
                  unit, price, explanation, note, currency, **kwargs):
        now = str(datetime.now()).split(".")[0]
        input_ = {
            "Sirket": company,
            "Urun_Kodu": product_code,
            "Ozel_Kod": str(special_code),
            "Miktar": amount,
            "Birim": unit,
            "Fiyat": price,
            "Aciklama": explanation,
            "Not": note,
            "Para_Birimi": currency,
            "Tarih": now,
        }
        input_.update(kwargs['item'])
        self.table_log.put_item(Item=input_)

    def query_log(self, special_code, company_name, start_date: str = "", end_date: str = ""):
        filtering_exp = Key('Ozel_Kod').eq(special_code)
        if special_code == "" and start_date == "" and end_date == "" and company_name == "":
            response = self.table_log.scan()
        elif special_code != "" and start_date == "" and end_date == "":
            response = self.table_log.query(KeyConditionExpression=filtering_exp)
        elif special_code != "" and start_date != "" and end_date == "":
            new_end_date = str(datetime.today() + timedelta(1))
            filtering_exp2 = Key('Tarih').between(start_date, new_end_date)
            response = self.table_log.query(KeyConditionExpression=filtering_exp & filtering_exp2)
        elif special_code != "" and start_date != "":
            filtering_exp2 = Key('Tarih').between(start_date, end_date)
            response = self.table_log.query(KeyConditionExpression=filtering_exp & filtering_exp2)
        elif company_name != "" and special_code == "" and start_date != "" and end_date != "":
            filtering_exp2 = Key('Tarih').between(start_date, end_date)
            response = self.table_log.scan(FilterExpression=Attr('Sirket').eq(company_name) & filtering_exp2)
        elif company_name != "" and special_code == "" and start_date != "" and end_date == "":
            new_end_date = str(datetime.today() + timedelta(1))
            filtering_exp2 = Key('Tarih').between(start_date, new_end_date)
            response = self.table_log.scan(FilterExpression=Attr('Sirket').eq(company_name) & filtering_exp2)
        else:
            response = self.table_log.scan(FilterExpression=Attr('Sirket').eq(str(company_name)))
        currency_list = ["₺(TL)", "$(USD)", "€(EUR)"]
        price_list = [0.0, 0.0, 0.0]
        items = response["Items"]
        for i in currency_list:
            for k in items:
                if i == k["Para_Birimi"]:
                    if i == "₺(TL)":
                        price_list[0] += float(k["Fiyat"])
                    elif i == "$(USD)":
                        price_list[1] += float(k["Fiyat"])
                    else:
                        price_list[2] += float(k["Fiyat"])
        return items, list(items[-1].keys()), price_list

    def update_product(self, product, key_list, value_list):
        ingredients_dict = self.query_product(product)
        for i in range(len(value_list)):
            ingredients_dict[0]["Icindekiler"][key_list[i]][0] = value_list[i]
        self.table_product.update_item(
            Key={
                'Urun_Ismi': product
            },
            UpdateExpression='SET Icindekiler = :Icindekiler',
            ExpressionAttributeValues={
                ':Icindekiler': ingredients_dict[0]["Icindekiler"]
            }
        )

    def update_database_from_excel(self, excel_list: dict):
        for i in range(len(excel_list)):
            new_special_code = excel_list[i][0]
            old_amount = self.get_amount(new_special_code)
            new_explanation = excel_list[i][2]
            new_unit = excel_list[i][3]
            if old_amount != 0.0:
                new_amount = float(old_amount) + float(excel_list[i][1])
                self.update_stock(new_special_code, str(new_amount), new_explanation)
            else:
                new_amount = 0.0 if excel_list[i][1] == "-" else float(excel_list[i][1])
                self.open_new_stock(special_code=new_special_code,
                                    unit=new_unit,
                                    amount=new_amount,
                                    explanation=new_explanation)

    def create_excel(self):
        """
        Create excel all log database.
        :return:
        """
        path = os.getcwd().replace("\\", "/")
        filename = 'stok_log.xlsx'
        response = self.table_log.scan()
        items = response["Items"]
        df = pd.DataFrame(items)
        keys = list(df.keys())
        df[keys[0]], df['Ozel_Kod'] = df['Ozel_Kod'], df[keys[0]]
        special_code_index = keys.index('Ozel_Kod')
        keys[special_code_index], keys[0] = keys[0], keys[special_code_index]
        df.columns = keys
        df.to_excel(excel_writer=filename, index=False, float_format="%.3f")
        return path, filename

    def read_excel(self, filename):
        """
        Read excel and upload to database.
        :param filename: The name of the file to be uploaded. Ex.: temp (without extension)
        :return:
        """
        df = pd.read_excel(io=filename)
        df.dropna(inplace=True, how='all')
        df = df.to_dict()
        items = {}
        keys = list(df.keys())
        update_stock_list = {}
        keys.remove('Ozel_Kod')
        for i in range(len(df['Ozel_Kod'])):
            items['Ozel_Kod'] = df['Ozel_Kod'][i]
            for key in keys:
                if str(df[key][i]) == 'nan':
                    df[key][i] = '-'
                if key == 'Tarih':
                    df[key][i] = str(datetime.now()).split(".")[0]
                items[key] = str(df[key][i])
            self.table_log.put_item(Item=items)
            update_stock_list[i] = [df['Ozel_Kod'][i],
                                    df['Miktar'][i] if df['Miktar'][i] != '-' else 0.0,
                                    df['Aciklama'][i],
                                    df['Birim'][i]]
            items.clear()
        return self.update_database_from_excel(update_stock_list)

    def create_product(self, product):
        ingredients = self.query_product(product)[0]["Icindekiler"]
        name_list = list(ingredients.keys())
        if self.control_amount(name_list, ingredients):
            for i in name_list:
                amount = self.get_amount(i)
                amount = float(amount) - float(ingredients[i][0])
                self.table_stock.update_item(
                    Key={
                        'Ozel_Kod': i
                    },
                    UpdateExpression='SET Miktar = :Miktar',
                    ExpressionAttributeValues={
                        ':Miktar': str(amount),
                    }
                )
            return 1
        else:
            return 0

    def control_amount(self, list_name: list, item: list):
        for name in list_name:
            amount_f = self.get_amount(name)
            amount_s, amount_f = float(item[name][0]), float(amount_f)
            if amount_f < amount_s:
                return False
        else:
            return True

    def get_parameters(self):
        response = self.table_input.scan(
            AttributesToGet=['Label_name', 'input_structure']
        )

        items = response['Items']
        return items

    def set_parameters(self, label_name):
        self.table_input.put_item(
            Item={
                'Label_name': label_name,
                'input_structure': f'<label for="new_">{label_name}:</label><br><input type="text" name="new_1" '
                                   f'id="new_"> <input type="hidden" name="label" value="{label_name}">'

            }
        )

    def delete_product(self, product):
        self.table_product.delete_item(Key={'Urun_Ismi': product})
        with open("products.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            data.pop(product)
        with open("products.json", "w", encoding="utf-8") as w:
            json.dump(data, w)

    def stock_excel(self):
        """
        Create excel all log database.
        :return:
        """
        path = os.getcwd().replace("\\", "/")
        filename = 'stok.xlsx'
        response = self.table_stock.scan()
        items = response["Items"]
        df = pd.DataFrame(items)
        keys = list(df.keys())
        df[keys[0]], df['Ozel_Kod'] = df['Ozel_Kod'], df[keys[0]]
        special_code_index = keys.index('Ozel_Kod')
        keys[special_code_index], keys[0] = keys[0], keys[special_code_index]
        df.columns = keys
        df.to_excel(excel_writer=filename, index=False, float_format="%.3f")
        return path, filename
