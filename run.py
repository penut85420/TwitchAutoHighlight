import json
import os
import subprocess

import requests
import threading

url_begin = "https://api.twitch.tv/v5/videos/%s/comments?client_id=%s"
url_next = "https://api.twitch.tv/v5/videos/%s/comments?client_id=%s&cursor=%s"

def get_video(video_id):
    print('Get VOD %s' % video_id)
    subprocess.call([
        './twitch_concat', '-vod', video_id, 
        '-start', '0 6 0', '-end', '10 0 0',
        '-quality', 'chunked', '-max-concurrent-downloads', '6'
    ])

def get_comments(video_id, client_id):
    print('Get comments of VOD %s' % video_id)
    # Get first comments
    r = requests.get(url_begin % (video_id, client_id))
    j = json.loads(r.text)

    # Output messages to log
    msglog = open('tmp_msg.log', 'w', encoding='utf-8')
    for m in j['comments']:
        msglog.write(str(m['content_offset_seconds']) + '\t' + m['message']['body'] + '\n')

    # Keep logging
    while j.get('_next', None):
        # print(j['_next'], end='\r')
        r = requests.get(url_next % (video_id, client_id, j['_next']))
        j = json.loads(r.text)
        for m in j['comments']:
            msglog.write(str(m['content_offset_seconds']) + '\t' + m['message']['body'] + '\n')

    msglog.close()
    print('\n\nGet comments done!')

def analysis(keywords):
    print('\nRetriveing messages')
    fout = open('msg_retrieve.log', 'w', encoding='utf-8')
    finn = open('tmp_msg.log', 'r', encoding='utf-8')
    for line in finn:
        for w in keywords:
            if w in line: fout.write(line)
    fout.close()
    finn.close()

def clustering(group_gap):
    print('\nClustering retrieved messages')

    finn = open('msg_retrieve.log', 'r', encoding='utf-8')
    fout = open('msg_group.log', 'w', encoding='utf-8')
    pre = 0
    count = 0
    fout.write('%.3f\t[Group]\t' % pre)
    for line in finn:
        if line.strip() == '': continue
        s, _ = line.split('\t')
        s = float(s)
        if s - pre > group_gap:
            fout.write(str(count) + '\n')
            fout.write('%.3f\t[Group]\t' % s)
            count = 0
        count += 1
        pre = s
    fout.write(str(count))

    finn.close()
    fout.close()
    print('\nMessage preprocessing done')

def make_clips(video_id):
    print('Making clips')
    clips_list = list()

    if not os.path.exists('./clips'):
        os.mkdir('./clips')

    with open('msg_group.log', 'r', encoding='utf-8') as fin:
        count = 1
        for line in fin:
            if line.strip() == '': continue
            print(line)
            t, _, n = line.split('\t')
            try: n = int(n)
            except: n = 0
            if n > 10:
                t = float(t)
                print(t - 30.0)
                subprocess.call([
                    'ffmpeg', '-i', '%s.mp4' % video_id, 
                    '-ss', str(t-20-360), '-t', '35', 
                    '-c', 'copy', 'clips/cut%d.mp4' % count
                ])
                clips_list.append('clips/cut%d.mp4' % count)
                count += 1
    
    return clips_list

def concat_all(clips_list):
    with open('in.txt', 'w', encoding='utf-8') as fout:
        for clip in clips_list:
            fout.write("file '%s'\n" % clip)
    
    subprocess.call(['ffmpeg', '-f', 'concat', '-i', 'in.txt', '-c', 'copy', 'all.mp4'])

def analysis_comments(video_id, client_id, keywords, group_gap):
    get_comments(video_id, client_id)
    analysis(keywords)
    clustering(group_gap)

if __name__ == "__main__":
    
    # video_id = '360257927'
    video_id = '341780306'
    # client_id = '2bkk0r1860f7a9j3mo2leulxkm1dyr'
    # keywords = ['777', '555']
    # group_gap = 30.0

    # if os.path.exists(video_id + '.mp4'):
    #     os.remove(video_id + '.mp4')

    # t1 = threading.Thread(target=get_video, args=(video_id, ))
    # t2 = threading.Thread(target=analysis_comments, args=(video_id, client_id, keywords, group_gap, ))
    
    # t1.start()
    # t2.start()

    # t1.join()
    # t2.join()
    # clustering(30.0)
    clips_list = make_clips(video_id)
    concat_all(clips_list)

    print("\nRun all done!")