import os
import time
import requests
from mutagen.mp3 import MP3, EasyMP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, APIC, USLT
from mutagen.mp4 import MP4, MP4Cover
from yandex_music import Client, Track
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter, NestedCompleter, PathCompleter
from prompt_toolkit.history import FileHistory 
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from pathlib import Path
from datetime import datetime
from yandex_music import Client
from os import getcwd, chdir, mkdir, listdir, path, rmdir
from shutil import rmtree
import json 


def download_track_full(client, id_track, nomer, download_path="."):
    """
    Скачивает трек со всеми метаданными (исполнитель, альбом, обложка, текст) в указанную папку.
    """
    # --- 1. Метаданные ---
    track = client.tracks(id_track)[0]
    title = track.title or "Unknown"
    artists = ", ".join(a.name for a in track.artists) if track.artists else "Unknown"
    album = track.albums[0].title if track.albums else None
    year = track.albums[0].year if track.albums else None
    track_num = track.albums[0].track_position if track.albums else None

    # --- 2. Прямая ссылка на аудио ---
    info = sorted(track.get_download_info(client), key=lambda x: x.bitrate_in_kbps, reverse=True)
    if not info:
        print(f"Нет ссылок для {title}")
        return
    best = info[0]
    audio_resp = requests.get(best.direct_link)
    audio_resp.raise_for_status()
    ext = 'mp3' if best.codec == 'mp3' else 'm4a'
    tmp_file = f"__tmp_{track.id}.{ext}"

    with open(tmp_file, 'wb') as f:
        f.write(audio_resp.content)

    # --- 3. Обложка ---
    cover_data = None
    try:
        cover_url = f"https://{track.cover_uri.replace('%%', '400x400')}"
        cover_data = requests.get(cover_url).content
    except:
        pass

    # --- 4. Внедрение тегов ---
    if ext == 'mp3':
        tags = ID3()
        tags.add(TIT2(encoding=3, text=title))
        tags.add(TPE1(encoding=3, text=artists))
        if album: tags.add(TALB(encoding=3, text=album))
        if year: tags.add(TDRC(encoding=3, text=str(year)))
        if track_num: tags.add(TRCK(encoding=3, text=str(track_num)))
        if cover_data: tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_data))
        try:
            lyrics = track.get_lyrics()
            if lyrics and lyrics.lyrics:
                tags.add(USLT(encoding=3, lang='eng', desc='Lyrics', text=lyrics.lyrics))
        except: pass
        tags.save(tmp_file)

    elif ext == 'm4a':
        audio = MP4(tmp_file)
        audio['\xa9nam'] = title
        audio['\xa9ART'] = artists
        if album: audio['\xa9alb'] = album
        if year: audio['\xa9day'] = str(year)
        if track_num: audio['trkn'] = [(track_num, 0)]
        if cover_data:
            audio['covr'] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
        try:
            lyrics = track.get_lyrics()
            if lyrics and lyrics.lyrics:
                audio['\xa9lyr'] = lyrics.lyrics
        except: pass
        audio.save()

    # --- 5. Финальное имя и перемещение ---
    safe_name = f"{nomer}_{id_track}_{artists}_{title}.{ext}"
    safe_name = "".join(c for c in safe_name if c not in r'\/:*?"<>|')
    final_path = os.path.join(download_path, safe_name)
    os.replace(tmp_file, final_path)
    time.sleep(5) 
    return final_path

def list_id_tracks_playlist(client, kind, uid):
    return [i["track"]["id"] for i in client.users_playlists(kind, uid).tracks]

def list_id_tracks_album(client, album_id):
    return [i["track"]["id"] for i in client.albums_with_tracks(album_id).tracks]

def install_list_tracks(client, list_tracks):
    #try:
        numer = 1

        id_install_tracks = {}
        for install_track in listdir():
            id_install_tracks[install_track.split("_")[1]] = install_track

        for track_id in list_tracks:
            if track_id in id_install_tracks:
                if json_config["delete"] == 2:
                    os.remove(id_install_tracks[track_id])
                    download_track_full(client, track_id, numer)
                    numer += 1
                elif json_config["delete"] == 3:
                    os.replace(id_install_tracks[track_id], f"{numer}_{'-'.join(id_install_tracks[track_id].split('_')[1:])}")
                    numer += 1
            else:
                download_track_full(client, track_id, numer)
                numer += 1
    #except:
    #    print(f"Ошибка при установке трека")
        
def install_playlist(client, kind, uid):
    try:
        print(f"    Начало установки: {json_name_id_playlists[kind]}")
        if json_name_id_playlists[kind] in listdir():
            print("        Плейлист найден в скачаном")
            if json_conf["delete"] == 1:
                print("     Найден скаченный плелист. Переустановка") 
                rmtree(json_name_id_playlists[kind])
                mkdir(json_name_id_playlists[kind])
            elif json_conf["delete"] == 0:
                print("     Найден  скаченный плейлист. Пропускается")
                return True
        else:
            mkdir(json_name_id_playlists[kind])
        chdir(json_name_id_playlists[kind])

        list_tracks_install =  list_id_tracks_playlist(client, kind, uid) 
        install_list_tracks(client, list_tracks_install)

        return True

    except Exception as e:
        print(f"Ошибка при скачивании плейлиста: {e}")
        return 0

def install_album(client, album_id):
    try:
        print(f"    Начало установки: {json_name_id_like_albums[album_id]}")
        if json_name_id_like_albums[albim_id] in listdir():
            print("        Плейлист найден в скачаном")
            if json_conf["delete"] == 1:
                print("     Найден скаченный плелист. Переустановка") 
                rmtree(json_name_id_like_albums[albim_id])
                mkdir(json_name_id_like_albums[albim_id])
            elif json_conf["delete"] == 0:
                print("     Найден  скаченный плейлист. Пропускается")
                return True
        else:
            mkdir(json_name_id_like_albums[albim_id])
        chdir(json_name_id_like_albums[albim_id])

        list_tracks_install =  list_id_tracks_album(client, album_id)
        install_list_tracks(client, list_tracks_install)

        return True

    except Exception as e:
        print(f"Ошибка при скачивании альбома: {e}")
        return 0

def get_prompt():
    global ac_stat
    """Создам промт для строки терминала"""
    now = datetime.now().strftime("%H:%M:%S")
    
    return HTML(f"[{now}] {ac_stat["account"]["login"]} <blinking>></blinking> ")



def repl(client):

    text_help = '''
    Приветствую вас в help установщика Яндекс музыки.

    ПО работает по принципу консольной строки.
    Укажите путь и добавте в список на установку плейлисты и альбомы, после чего установите все выбранное.

    При первом запуске программа запустит авторизацию, но так же можно это сделать самостоятельно с помощью create_key.py

    Доступные команды:
        Работа с файлами:
            sp - выбрать путь, по которому будет установка
            where - посмотреть путь, по котрому будет установка
            ls - посмотреть сущуствующие объекты  по  пути установки
        Работа с альбомами/плейлистами:
            addplay - добавить плейлист. Можно добавить несколько через "; "
            addalb - добавить альбом. Можно добавить несколько через "; "
            cil - очистить список на установку. Можно добавить albums или playlists
            linst - посмотреть список плейлистов и альбомов на установку
            install - установить все выбранное
        Остальные комманды:
            help - вывести эту справку
            q, exit - выйти из программы установки
    '''

    custom_style = Style([
        ('blinking', 'blink'),
    ])

    history_file = path.expanduser('~/.local/share/download_music/histiry')

    history_path = Path(history_file)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    # 3. Теперь можно безопасно создавать FileHistory
    history = FileHistory(history_file)
    cmd_session = PromptSession(
        completer=completer,
        history=history,
        style=custom_style,
        auto_suggest=AutoSuggestFromHistory(),
    )

    install_list_playlists = []
    install_list_albums = []

    while True:
        try:
            user_input_1 = cmd_session.prompt(get_prompt)
        except (KeyboardInterrupt, EOFError):
            continue
        
        user_input = user_input_1.strip()
        list_user_input = user_input.split(" ")

        match list_user_input[0]:
            case "exit": #Конец выолнения программы
                exit()
            case "q": #Конец выолнения программы
                exit()
            case "addplay": #Добавить плейлист в список на скачивание
                for i in " ".join(list_user_input[1:]).split("; "):
                    if i in name_playlists:
                        install_list_playlists.append(json_id_name_playlists[i])
                        print(f"Плейлист {i} добавлен")
                    else:
                        print(f"Плейлист {i} не добавлен. Такого плейлиста нет")
            case "addalb": #Добавить альбом в список на скачивание
                for i in " ".join(list_user_input[1:]).split("; "):
                    if i in name_like_albums:
                        install_list_albums.append(json_id_name_like_albums[i])
                        print(f"Альбом {i} добавлен")
                    else:
                        print(f"Альбом {i} не добавлен. Такого плейлиста нет")
            case "cil": #Очистить список на скачивание
                if list_user_input[1] ==  "albums":
                    install_list_albums = []
                    print("Список плейлистов на установку очищен")
                elif list_user_input[1] == "playlists":
                    install_list_playlists = []
                    print("Список альбомов на установку очищен")
                else:
                    install_list_albums = []
                    print("Список плейлистов на установку очищен")
                    install_list_playlists = []
                    print("Список альбомов на установку очищен")
            case "linst": #Посмотреть списки на скачивание
                f = 1
                if len(install_list_playlists) > 0:
                    print("Список плейлистов на установку:")
                    for playlist in install_list_playlists:
                        print("     " + json_name_id_playlists[playlist])
                        f = 0
                
                if len(install_list_albums) > 0:
                    print("Список альбомов на установку:")
                    for album in install_list_albums:
                        print("     " + json_name_id_like_albums[album])
                        f = 0
            
                if f:
                    print("Список на установку пуст")
            case "install": #Установка списков на скачивание
                f = 1
                if len(install_list_playlists) > 0:
                    print("Список плейлистов на установку:")
                    for playlist in install_list_playlists:
                        print("     " + json_name_id_playlists[playlist])
                        f = 0
                
                if len(install_list_albums) > 0:
                    print("Список альбомов на установку:")
                    for album in install_list_albums:
                        print("     " + json_name_id_like_albums[album])
                        f = 0
            
                if f:
                    print("Список на установку пуст")
                    continue

                if len(install_list_playlists) > 0:
                    print("Установка плейлистов:")
                    for playlist in install_list_playlists:

                        if install_playlist(client, playlist, uid):
                            pass
                        else:
                            error_list[0].append(playlist)
                        
                        chdir(save_path)
                        

                if len(install_list_albums) > 0:
                    print("Установка альбомов:")
                    for album in install_list_albums:
                        if install_album(client, album):
                            pass
                        else:
                            error_list[1].append(album)
                        
                        chdir(save_path)

                    
            case "sp": #Сменить путь для скачивания
                if list_user_input[1][0] == "/":
                    save_path = list_user_input[1]
                else:
                    save_path += list_user_input[1]
                chdir(save_path)
            case "where": #Посмотреть путь для скачивания
                print("Путь для сохранения файлов:")
                print("     " + getcwd()) 
            case "help":
                print(text_help)
            case "ls": #Посмотреть файлы по пути для скачивания
                print(listdir()) 
            case _: #Обработка неизвестных комманд
                print("Неизвестная команда")

if __name__ == "__main__":
    with open("config.json", "r") as file:
        json_conf = json.load(file)

    if "env.json" in listdir():
        with open("env.json", "r") as file:
            json_env = json.load(file)
    else:
        print("Вы не авторизованы. Привижите аккаунт:")
        def on_code(code):
            print(f'Откройте {code.verification_url} и введите код: {code.user_code}')


        client = Client()
        token = client.device_auth(on_code=on_code)
        print(f'access_token:  {token.access_token}')
        print(f'refresh_token: {token.refresh_token}')
        print(f'expires_in:    {token.expires_in}')

        print("Сохранение в env.json")
        with open("env.json", "w") as file:
            json_env = {
                "access_token":  token.access_token,
                "refresh_token": token.refresh_token, 
                "expires_in":    token.expires_in

            }
            dump(json_env, file) 


    client = Client(json_env["access_token"]).init()

    print(f"Вы удачно авторизовались")
    ac_stat = client.account_status()
    uid = ac_stat["account"]["uid"]
    print(f"    Логин: {ac_stat['account']['login']}")

    playlists = client.users_playlists_list()
    liked_albums = client.users_likes_albums()

    name_playlists = [i["custom_wave"]["title"] for i in playlists]
    name_like_albums = [i["album"]["title"] for i in liked_albums]

    error_list = [[],[]]
    
    json_id_name_playlists = {}
    json_id_name_like_albums = {}
    json_name_id_playlists = {}
    json_name_id_like_albums = {}
    for playlist in playlists:
        json_id_name_playlists[playlist["custom_wave"]["title"]] = playlist["kind"]
        json_name_id_playlists[playlist["kind"]] = playlist["custom_wave"]["title"]
    for album in liked_albums:
        json_id_name_like_albums[album["album"]["title"]] = album["album"]["id"]
        json_name_id_like_albums[album["album"]["id"]] = album["album"]["title"]

    save_path = getcwd()

    completer = NestedCompleter.from_nested_dict({
        'sp': PathCompleter(only_directories=True, expanduser=True),
        'addplay': WordCompleter(name_playlists, ignore_case=True),
        'addalb': WordCompleter(name_like_albums, ignore_case=True),
        'cil' : WordCompleter(["albums", "playlists"], ignore_case=True),
        'exit': None,
        'q' : None,
        'install' : None,
        'linst' : None,
        'where' : None,
        'ls' : None,
    })
    repl(client)



