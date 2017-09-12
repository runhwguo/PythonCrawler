from urllib import request
from bs4 import BeautifulSoup
import re
import os
import string

BASE_URL = 'http://music.baidu.com'
MUSIC_URL = BASE_URL + '/tag/%E7%BB%8F%E5%85%B8%E8%80%81%E6%AD%8C'
PAGE_SIZE = 20
MUSIC_PAGE_PARAM = '?size=%s&start=' % PAGE_SIZE
LYRIC_DIR = 'lyric'

CHINESE_PUNCTUATION = r'＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏！？｡。'

'''
bs4:
    https://www.crummy.com/software/BeautifulSoup/bs4/doc/index.zh.html
'''


def get_data_from_url(url):
    try:
        response = request.urlopen(url)
        data = response.read().decode()
    except Exception as ex:
        # BaiDu 404
        print(url, ex)
        data = None
    return data


def clear_common_data(data):
    # clear() （） [] <>
    result = re.sub(r'\(.*\)', '', data)
    result = re.sub(r'（.*）', '', result)
    result = re.sub(r'\[.*\]', '', result)
    result = re.sub(r'<.*>', '', result)
    result = re.sub(r'\s{2,}', '', result)

    return result


def clear_punctuation_data(data):
    # clear 标点符号
    translator = str.maketrans('', '', string.punctuation)
    result = data.translate(translator)

    translator = str.maketrans('', '', CHINESE_PUNCTUATION)
    result = result.translate(translator)

    return result


def clear_data_lyric(data):
    '''
    词 曲 演唱 编 | : ：delete
    歌词字符少于 一定值 dirty data 150
    男/女/合|:： ''
    歌手当行之前 remove
    最后一个行歌手名之后 remove
    :/：之前remove
    :param data:
    :return:
    '''

    # clear 词/曲/演唱/编/--END--
    lyric_head = r'(.*词[:：].*)|(.*曲[:：].*)|(.*演唱[:：].*)|(.*编[:：].*)|(.*end.*)'

    messy_message = r'.*[:：].*'

    result = clear_common_data(data)
    lyric_lines = result.split('\n')
    while True:
        for line_num in range(len(lyric_lines)):
            line = lyric_lines[line_num]
            if re.match(lyric_head, line, re.I):
                lyric_lines = lyric_lines[line_num + 1:]
                break
            if re.match(messy_message, line):
                lyric_lines.remove(line)
                break
            if line == '':
                lyric_lines.remove(line)
                break

        if line_num == len(lyric_lines) - 1:
            break

    result = '\n'.join(lyric_lines)

    result = clear_punctuation_data(result)

    return result


if __name__ == '__main__':
    if not os.path.exists(LYRIC_DIR):
        os.makedirs(LYRIC_DIR)

    name_url = {}
    # 获取歌名和链接
    for index in range(17):
        html_data = get_data_from_url(''.join([MUSIC_URL, MUSIC_PAGE_PARAM, str(PAGE_SIZE * index)]))
        if html_data:
            soup = BeautifulSoup(html_data, 'html.parser')
            song_a_links = soup.find_all('a', attrs={'data-film': 'null'})

            for a_link in song_a_links:
                link = a_link.get('href', None)
                song_name = a_link.text
                song_name = clear_common_data(song_name)
                if re.match('[\u4e00-\u9fff]+', song_name):
                    if link and song_name:
                        if song_name not in name_url:
                            name_url[song_name] = link
                            print('链接 -> ', song_name, link)

    # 洗歌词(去掉 歌词时间、男/女、空行) 纯歌词
    for key, value in name_url.items():
        html_lyric = get_data_from_url(BASE_URL + value)
        if html_lyric:
            soup = BeautifulSoup(html_lyric, 'html.parser')
            lyric_div = soup.find_all('div', id='lyricCont')
            try:
                # 纯音乐 没有歌词
                lyric_link = lyric_div[0].get('data-lrclink', None)

                # print(lyric_link)
                data_lyric = get_data_from_url(lyric_link)
                with open(os.path.join(LYRIC_DIR, key + '_origin.txt'), 'w') as f:
                    f.write(data_lyric)
                # 再强的洗数据规则，也干不过傻逼没有统一标准的歌词格式
                data_lyric = clear_data_lyric(data_lyric)
                if len(data_lyric) > 30:
                    with open(os.path.join(LYRIC_DIR, key + '.txt'), 'w') as f:
                        f.write(data_lyric)
                        print('存储 -> ', key)
                else:
                    print('歌词太短 -> ' + data_lyric)
            except Exception as e:
                print(key, value, e)
    print(len(name_url))
