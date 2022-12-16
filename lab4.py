# -*- coding: utf-8 -*-
import operator

import nltk
import sqlite3

from tkinter import *
from tkinter import filedialog as fd



from googletrans import Translator
from pymorphy2 import MorphAnalyzer


db = sqlite3.connect('db.sqlite3')
cursor = db.cursor()

analyzer = MorphAnalyzer()

translator = Translator()

grammar = r"""
        P: {<PRCL|PREP>}
        V: {<VERB|INFN>}
        N: {<NOUN|NPRO>}
        PP: {<P><N>}
        NP: {<N|PP>+<ADJF|NUMR>+}
        NP: {<ADJF|NUMR>+<N|PP>+}
        VP: {<NP|N><V>}
        VP: {<V><NP|N>}
        VP: {<VP><NP|N|GRND|PRTS|ADVB>}
        VP: {<NP|N|GRND|PRTS|ADVB><VP>}
        VP: {<VP><PP>}
        """


def tokenize_sentence(sentences):
    list_word = []
    for sent in nltk.sent_tokenize(sentences.lower()):
        for word in nltk.word_tokenize(sent):
            list_word.append(word)
    return list_word


def get_word_tag(text):
    list_word_with_tag = []
    list_word = tokenize_sentence(text)
    analyzer = MorphAnalyzer()
    for word in list_word:
        parse_word = analyzer.parse(word)[0]
        list_word_with_tag.append((word, parse_word.tag.POS))
    return list_word_with_tag


def draw_tree(text):
    if text != '':
        text.replace('\n', '')
        doc = get_word_tag(text)
        new_doc = []
        for item in doc:
            if item[0] not in [',', '.', '-', ':', ';', '?', '!']:
                new_doc.append(item)
        cp = nltk.RegexpParser(grammar)
        result = cp.parse(new_doc)
        result.draw()


def open_file_and_input_text():
    file_name = fd.askopenfilename(filetypes=(("Txt files", "*.txt"),))
    if file_name != '':
        with open(file_name, 'r') as file:
            text = file.read()
            text.replace('\n', '')
            text.replace('.', '. ')
            calculated_text.delete(1.0, END)
            calculated_text.insert(1.0, text)


def google_translate(text):
    sentence = []
    new_text = ''
    for sent in nltk.sent_tokenize(text):
        translate = translator.translate(sent,  'ru')
        sentence.append(translate.text)
        new_text += translate.text + ' '
    return sentence


def grammar_text(sent):
    word = {}
    text = ''.join(sent)
    list_word = text.split(' ')
    for item in list_word:
        if item not in word:
            word.update({item: 1})
        else:
            word[item] += 1
    sorted_word = sorted(word.items(), key=operator.itemgetter(1))
    new_list_word = []
    for item, _ in sorted_word:
        parse_word = analyzer.parse(item)[0]
        tag = parse_word.tag
        new_list_word.append((item, _, str(tag)))
    with open('translate.txt', 'w') as f:
        f.write(str(new_list_word))


def db_and_google_translate(text):
    phrase = []
    sentence = []
    new_text = ''
    for word in cursor.execute("SELECT * FROM Dict"):
        word = tuple([word[1], word[2]])
        phrase.append(word)
    for row in cursor.execute("SELECT * FROM Func"):
        row = tuple([row[1].replace('x1', '').replace('x2', '').replace('x3', ''),
                     row[2].replace('y1', '').replace('y2', '').replace('y3', '')])
        phrase.append(row)
    for sent in nltk.sent_tokenize(text):
        new_sent = ''
        i = 0
        while i < len(phrase):
            if phrase[i][1] in sent:
                sent.replace(phrase[i][1], phrase[i][0])
            i += 1
        new_sent_n = translator.translate(sent, 'ru')
        new_sent += new_sent_n.text
        sentence.append(new_sent)
        new_text += new_sent + ' '
    return sentence


def print_sentence(translator_name):
    child_window = Toplevel(root)
    child_window.title("Перевод")
    if translator_name == 'google':
        sentence = google_translate(text=calculated_text.get(1.0, END))
    else:
        sentence = db_and_google_translate(text=calculated_text.get(1.0, END))
    grammar_text(sentence)
    i = 0
    k = 0
    new_dict = {}
    while i < len(sentence):
        label_item = Label(child_window, text=str(i+1) + '. ' + sentence[i])
        label_item.grid(row=i, column=1)
        new_dict.update({i+1: sentence[i]})
        i += 1
        k = i
    number = Text(child_window, height=1, width=3)
    number.grid(row=k+1, column=1, sticky='nsew', rowspan=1, columnspan=1)
    button_draw = Button(child_window, text="Дерево", width=15, command=lambda: draw_tree(new_dict[int(number.get(1.0, END))]))
    button_draw.grid(row=k+2, column=1)


def add_trans_to_db(eng, rus):
    sql = 'INSERT INTO Dict(WrdEng, WrdRus) VALUES("' + str(eng.replace('\n', '')) \
          + '", "' + str(rus.replace('\n', '')) + '")'
    cursor.execute(sql)
    db.commit()


def add_trans():
    child_window = Toplevel(root)
    child_window.title("Перевод")
    label_rus = Label(child_window, text='русское слово')
    label_rus.grid(row=1, column=1)
    label_eng = Label(child_window, text='английское слово')
    label_eng.grid(row=1, column=0)
    text_eng = Text(child_window, height=1, width=20)
    text_eng.grid(row=2, column=0)
    text_rus = Text(child_window, height=1, width=20)
    text_rus.grid(row=2, column=1)
    button_add = Button(child_window, text="Добавить", width=15,
                         command=lambda: add_trans_to_db(text_eng.get(1.0, END),
                                                         text_rus.get(1.0, END)))
    button_add.grid(row=3, column=1)


root = Tk()
root.title("Перевод")
label = Label(root, text='Введите текст:')
label.grid(row=0, column=1)
calculated_text = Text(root, height=30, width=70)
calculated_text.grid(row=1, column=1, sticky='nsew', rowspan=3, columnspan=4)
button1 = Button(text="Перевод бд+google", width=15, command=lambda: print_sentence('bd'))
button1.grid(row=4, column=1)
button2 = Button(text="Перевод google", width=15, command=lambda: print_sentence('google'))
button2.grid(row=4, column=2)
button3 = Button(text="Открыть файл", width=11, command=open_file_and_input_text)
button3.grid(row=4, column=3)
button4 = Button(text="Добавить перевод", width=15, command=add_trans)
button4.grid(row=4, column=4)
root.mainloop()
