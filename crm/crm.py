import os
import time
import json
import signal
import hashlib
import webbrowser

from datetime import datetime
from tools import Tools, Secret
from send_mail import send_new_password
from flask import Flask, render_template, request, abort, session, redirect, url_for, send_from_directory

Tools = Tools()
PID = os.getpid()

webbrowser.open(Secret.url)
parameter = Secret.parameter

app = Flask(__name__)
app.secret_key = Secret.secret_key
app.jinja_env.globals.update(zip=zip)

username: None
service: None
user_type: None


@app.route('/yetki', methods=['POST'])
def authority():
    global username
    username = request.form.get('user_name')
    password_ = request.form.get('password').encode("utf-8")
    password = hashlib.sha256(password_).hexdigest()
    credential = Tools.query_authority(username)
    try:
        credential = dict(credential[0])
        registered_username, registered_password = credential['username'], credential['password']
        if username == registered_username and password == registered_password:
            session['user_name'] = username
            return redirect(url_for('index', parametre=parameter))
        else:
            return redirect(url_for('login', parametre=parameter))
    except IndexError:
        return redirect(url_for('index', parametre=parameter))


@app.route('/')
def index():
    global username, service, user_type
    if 'user_name' in session:
        username = str(session.get('user_name', None))
        service, add, stock, log_, user_type = Tools.get_param(username_=username)
        username = username.capitalize()
        today = datetime.today()
        created_prod = Tools.created_product_number()
        usernames, types, dates, times = Tools.get_recent_activity()
        products_number = Tools.number_of_products()
        number_of_users = Tools.users_number()
        return render_template("index.html", parametre=parameter, servis=service, ekle=add, stok=stock,
                               log=log_, username=username, date=today, usernames=usernames, types=types, dates=dates,
                               times=times, products_number=products_number, number_of_users=number_of_users,
                               created_prod=created_prod)
    elif Tools.auth():
        return redirect(url_for('login', parametre=parameter))
    else:
        return redirect(url_for('login'))


@app.route('/stok_takip')
def stock_tracking():
    if 'user_name' in session:
        username_ = str(session.get('user_name', None))
        service_, add, stock, log_, user_type_ = Tools.get_param(username_)
        username_ = username_.capitalize()
        return render_template('Stok_takip.html', parametre=parameter, servis=service_, ekle=add,
                               stok=stock, log=log_, username=username_)
    else:
        abort(403)


@app.route('/ekle')
def ekle():
    if 'user_name' in session:
        return render_template('ekle.html')
    else:
        abort(403)


@app.route('/ekle/kaydet', methods=['POST'])
def ekle_kaydet():
    if 'user_name' in session:
        b = request.form.get('sp_code')
        unit = request.form.get('unit')
        data = {'search_name': b}
        counter = 0
        with open("search_name.json", "r", encoding='utf-8') as newfile:
            list_ = eval(newfile.read())
            if data in list_:
                counter = 1
            if counter != 1:
                with open("search_name.json", "w", encoding='utf-8') as file:
                    list_.append(data)
                    json.dump(list_, file)
        Tools.open_new_stock(b, unit)
        Tools.recent_activity("Stok Kayıt Aç")
        return redirect(url_for('ekle'))
    else:
        abort(403)


@app.route('/profil')
def profile():
    username_ = str(session.get('user_name', None))
    email = Tools.get_email(username_)
    return render_template('profil.html', username=username_, email=email)


@app.route('/değiştir', methods=['POST'])
def change_func():
    new_password = request.form.get('password')
    email = request.form.get('email')
    username_ = str(session.get('user_name', None))
    if new_password == "":
        Tools.change("email", username_, email)
    else:
        new_password = hashlib.sha256(new_password.encode("utf-8")).hexdigest()
        Tools.change("password", username_, new_password)
    return redirect(url_for('profile'))


@app.route('/yeni_kullanıcı')
def new_user_func():
    if 'user_name' in session:
        return render_template("yeni_kullanıcı.html")
    else:
        return redirect(url_for('login'))


@app.route('/yeni_kullanıcı/kaydet', methods=['POST'])
def new_user_save_func():
    if 'user_name' in session:
        new_username = request.form.get('new_username')
        new_password = request.form.get('new_password')
        if new_password == "":
            new_password = hashlib.sha256(new_username.encode("utf-8")).hexdigest()
        else:
            new_password = hashlib.sha256(new_password.encode("utf-8")).hexdigest()
        new_service = request.form.get('servis')
        if new_service is None:
            new_service = 0
        new_stock = request.form.get('stok')
        if new_stock is None:
            new_stock = 0
        new_add = request.form.get('ekle')
        if new_add is None:
            new_add = 0
        new_log = request.form.get('log')
        if new_log is None:
            new_log = 0
        new_user_type = request.form.get('user_type')
        Tools.insert(new_username, new_password, new_service, new_add, new_stock, new_log, new_user_type)
        Tools.recent_activity("Yeni Kullanıcı Ekle")
        return redirect(url_for('new_user_func'))
    else:
        abort(403)


@app.route('/ürün')
def product_func():
    if 'user_name' in session:
        with open('products.json') as f:
            obj = json.load(f)
            list_ = list(obj.keys())
        return render_template("ürün.html", liste=list_)
    else:
        abort(403)


@app.route('/ürün_ekle')
def add_product_func():
    if 'user_name' in session:
        list_ = []
        with open('search_name.json') as f:
            obj = eval(f.read())
            for index_ in range(len(obj)):
                list_.append(obj[index_]["search_name"])
        return render_template("ürün_ekle.html", liste=list_)
    else:
        abort(403)


@app.route("/result", methods=['POST'])
def result_func():
    if 'user_name' in session:
        materials = {}
        product_name = request.form.get('urunAdi')
        materials_names = request.form.getlist('malzemeAdi[]')
        amounts = request.form.getlist('miktar[]')
        units = request.form.getlist('birim[]')
        for material_name, amount, unit in zip(materials_names, amounts, units):
            materials[material_name] = [amount, unit]
        data = {product_name: 0}
        with open("products.json", "r") as newfile:
            new_ = json.load(newfile)
            if product_name not in new_.keys():
                with open("products.json", "w") as file:
                    new_.update(data)
                    json.dump(new_, file)

        Tools.insert_products(product_name, materials)
        Tools.recent_activity("Ürün Ekle")
        return redirect(url_for('add_product_func'))
    else:
        abort(403)


@app.route("/create_products", methods=['POST'])
def create_product_func():
    if 'user_name' in session:
        try:
            option = request.form.get('choose')
            option_2 = request.form.get('update')
            product = request.form.get('ürün')
            if option is not None:
                alert = Tools.create_product(product)
                temp_list = []
                ingredients = Tools.query_product(product)
                ingredients_keys = list(ingredients[0]["Icindekiler"].keys())
                for i in ingredients_keys:
                    data = i + " : " + ingredients[0]["Icindekiler"][i][0] + " " + ingredients[0]["Icindekiler"][i][1]
                    temp_list.append(data)
                return render_template("ürün_oluştur.html", temp_list=temp_list, product=product,
                                       alert=alert)
            elif option_2 is not None:
                list_ = []
                temp_list = []
                birim = []
                ingredients = Tools.query_product(product)
                ingredients_keys = list(ingredients[0]["Icindekiler"].keys())
                for i in ingredients_keys:
                    data = ingredients[0]["Icindekiler"][i][0]
                    data_2 = ingredients[0]["Icindekiler"][i][1]
                    temp_list.append(data)
                    list_.append(i)
                    birim.append(data_2)
                session['names_list'] = list_
                session['product'] = product
                return render_template("product_update.html", liste=list_, temp_list=temp_list, product=product,
                                       birim=birim)
            else:
                Tools.delete_product(product)
                Tools.recent_activity("Ürün Sil")
                return redirect(url_for('product_func'))
        except:
            return redirect(url_for('product_func'))
    else:
        abort(403)


@app.route("/product_process", methods=['POST'])
def product_process():
    product = request.form.get('product')
    Tools.set_created_product_number()
    return redirect(url_for('product_func'))


@app.route("/update_product", methods=['POST'])
def update_product():
    list_ = session['names_list']
    product = session['product']
    session.pop('product', None)
    session.pop('name_list', None)
    value_list = []
    for i in list_:
        data = request.form.get(i)
        value_list.append(data)
    Tools.update_product(product, list_, value_list)
    return redirect(url_for('product_func'))


@app.route('/add_stock/save_stock', methods=['POST'])
def stock_add_save():
    if 'user_name' in session:
        data = request.form
        label_name = data.getlist("label")
        new_name = data.getlist("new_1")

        for i in label_name:
            Tools.set_parameters(i)

        session['label_name'] = label_name

        key_list = ['firma', 'urun_kod', 'kisa_kod', 'miktar', 'birim', 'fiyat', 'money_unit', 'aciklama', 'not',
                    'new_']

        for i in range(len(data) // 8):
            i = str(i + 1)
            company = data.get(key_list[0] + i)
            prod_code = data.get(key_list[1] + i)
            short_code = data.get(key_list[2] + i)
            amount = data.get(key_list[3] + i)
            unit = data.get(key_list[4] + i)
            price = data.get(key_list[5] + i)
            currency = data.get(key_list[6] + i)
            explanation = data.get(key_list[7] + i)
            note = data.get(key_list[9] + i)
            new = {}
            for new_ in range(len(new_name)):
                new[label_name[new_]] = new_name[new_]
            Tools.stock_log(company, prod_code, short_code, amount, unit, price, explanation, note, currency, item=new)
            amount_ = Tools.get_amount(short_code)
            new_amount = float(amount) + float(amount_)
            Tools.update_stock(short_code, new_amount, explanation)
        Tools.recent_activity("Stok Ekle")
        return redirect(url_for('stok'))
    else:
        abort(403)


@app.route('/login')
def login():
    if Tools.auth():
        return render_template("login.html")
    else:
        abort(403)


@app.route('/forget_password')
def reset_password_func():
    return render_template('password.html')


@app.route('/new_password', methods=['POST'])
def new_password_func():
    username_ = request.form.get('username')
    email = request.form.get('email')
    real_email = Tools.get_email(username_)
    if email == real_email:
        new_password = Tools.generate_password()
        new_password_db = hashlib.sha256(new_password.encode("utf-8")).hexdigest()
        Tools.change("password", username_, new_password_db)
        send_new_password(email, new_password)
    return redirect(url_for('login', parametre=parameter))


@app.route('/logout')
def logout():
    if Tools.auth():
        session.pop('user_name', None)
        return redirect(url_for('login', parametre=parameter))
    else:
        abort(403)


@app.route('/excel_process')
def excel_process():
    if 'user_name' in session:
        username_ = str(session.get('user_name', None))
        service_, add, stock, log_, user_type_ = Tools.get_param(username_)
        return render_template('excel.html', ekle=add, log=log_)
    else:
        abort(403)


@app.route('/create_excel')
def create_excel():
    path, filename = Tools.create_excel()
    return send_from_directory(path, filename, as_attachment=True)


@app.route('/upload', methods=['POST'])
def upload():
    excel_file = request.files['excel_file']
    path = os.getcwd() + "/upload/" + excel_file.filename
    excel_file.save(path)
    Tools.read_excel(path)
    os.remove(path)
    return redirect(url_for('excel_process'))


@app.route('/add_stock')
def stok():
    if 'user_name' in session:

        information = Tools.get_parameters()
        name_list = []
        with open("search_name.json", "r", encoding='utf-8') as newfile:
            search_names = eval(newfile.read())
            for i in search_names:
                i = dict(i)
                name_list.append(i['search_name'])
        return render_template('stok_ekle.html', name_list=name_list, informations=information)
    else:
        return redirect(url_for('login'))


@app.route('/show_stock')
def show_stock():
    data = Tools.get_stock()
    return render_template('stock_show.html', data=data)


@app.route('/stock_excel')
def stock_excel():
    path, filename = Tools.stock_excel()
    return send_from_directory(path, filename, as_attachment=True)
    

@app.route('/show_stock_log')
def show_stock_log():
    if 'user_name' in session:
        name_list = []
        stock_log = session.get('stock_log')
        column_name_list = session.get('column_name_list')
        currency_list = session.get('currency_list')
        company_name = session.get('company_name')
        min_price_ = session.get('min_pricee')
        max_price_ = session.get('max_pricee')
        session.pop('stock_log', None)
        session.pop('column_name_list', None)
        session.pop('currency_list', None)
        session.pop('company_name', None)
        session.pop('min_pricee', None)
        session.pop('max_pricee', None)
        with open("search_name.json", "r", encoding='utf-8') as newfile:
            search_names = eval(newfile.read())
            for i in search_names:
                i = dict(i)
                name_list.append(i['search_name'])
            return render_template('show_stock_log.html', name_list=name_list, stock_log=stock_log,
                                   column_name_list=column_name_list, currency_list=currency_list,
                                   company_name=company_name,
                                   min_pricee=min_price_, max_pricee=max_price_)


@app.route('/show_stock_log/show_log', methods=['POST'])
def show_log():
    try:
        sp_code = request.form.get('sp_code')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        company_name = request.form.get('companyy')
        min_price_ = request.form.get('min_price')
        max_price_ = request.form.get('max_price')

        stock_log, column_name_list, currency_list = Tools.query_log(sp_code, company_name, start_date, end_date)
        session['stock_log'] = stock_log
        session['column_name_list'] = column_name_list
        session['currency_list'] = currency_list
        session['company_name'] = company_name
        session['min_pricee'] = min_price_
        session['max_pricee'] = max_price_
        return redirect(url_for('show_stock_log'))
    except:
        return redirect(url_for('show_stock_log'))


@app.route('/log')
def log():
    if 'user_name' in session:
        with open('products.txt', 'r') as file:
            data = file.read().replace('\n', '<br>')
            return render_template('log.html', data=data)
    else:
        abort(403)


@app.route('/exit')
def exit_program():
    if Tools.auth():
        try:
            if 'user_name' in session:
                session.clear()
                time.sleep(3)
                return os.kill(PID, signal.SIGTERM)
        except KeyError:
            return redirect(url_for('login', parametre=parameter))
    else:
        abort(403)


if __name__ == '__main__':
    app.run(port=5454, host='0.0.0.0', debug=True)
