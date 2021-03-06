import subprocess
from CMi.utils import ListItem
from django.db import IntegrityError
from CMi.engine import playable_path, canonical_format
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from CMi.tvshows.models import *
import tvdb
from math import ceil

def index(request, category_id=None):
    category = Category.objects.get(pk=category_id) if category_id else None
    shows = sorted(Show.objects.filter(category=category), key=lambda x: title_sort_key(x.name))
    shows = [
        ListItem(
            '/tvshows/%s' % show.pk,
            show.name,
            show.unwatched_episodes().count(),
        )
        for show in shows if show.watchable_episodes()]
    height = 11
    width = int(ceil(len(shows) / float(height)))
    rows = [[None for _ in range(width)] for _ in xrange(height)]
    for i, show in enumerate(shows):
        x = i % height
        rows[x][i / height] = show
    return render(request, 'tvshows/index.html', {
        'title': 'TV Shows' if category is None else category.name,
        'rows': rows,
        'suggested_shows': SuggestedShow.objects.filter(ignored=False)})

def episode_list(request, show_id):
    def episodes_to_rows(eps):
        season_to_column = {x: [] for i, x in enumerate(sorted({x.season for x in eps}))}
        for ep in eps:
            season_to_column[ep.season].append(ep)

        width = len(season_to_column.keys())
        height = max([len(column) for column in season_to_column.values()])
        rows = [
            [None for _ in xrange(width)] for _ in xrange(height)
        ]
        for column_i, (_, column) in enumerate(sorted(season_to_column.items())):
            for row_i, e in enumerate(column):
                rows[row_i][column_i] = e
        return rows

    show = get_object_or_404(Show, pk=show_id)
    next_episode = None
    try:
        next_episode = show.watchable_episodes().order_by('watched_at', 'season', 'episode', 'aired')[0]
        if next_episode == show.watchable_episodes()[0]:
            next_episode = None
        else:
            next_episode.episode = 'Next: %s' % next_episode.episode
    except IndexError:
        pass

    eps = list(show.watchable_episodes())
    if not eps:
        return HttpResponse(':back')
    rows = episodes_to_rows(eps)
    return render(request, 'tvshows/show.html', {
        'show': show,
        'rows': rows,
        'next_episode': next_episode,
        'seasons': [e.season for e in rows[0]],
    })

def play_episode(request, show_id, episode_id):
    episode = get_object_or_404(Episode, pk=episode_id)
    path = playable_path(episode.filepath)
    print 'playing ', episode, 'at', path
    subprocess.call(['open', 'CMiVideoPlayer://%s?seconds=%s&callback=tvshows/%s/%s' % (path, episode.position, episode.show.pk, episode.pk)])
    return HttpResponse(':back')

def episode_ended(request, show_id, episode_id):
    episode = get_object_or_404(Episode, pk=episode_id)
    episode.watched = True
    episode.watched_count += 1
    episode.position = 0
    episode.watched_at = datetime.now()
    episode.save()
    return HttpResponse(':nothing')

def episode_position(request, show_id, episode_id, position):
    episode = get_object_or_404(Episode, pk=episode_id)
    episode.position = position
    episode.save()
    return HttpResponse(':nothing')

def suggested_shows(request):
    return render(request, 'tvshows/suggested_shows.html', {'suggested_shows': SuggestedShow.objects.filter(ignored=False)})

def add_suggested_show(request, suggested_show_id, option):
    s = SuggestedShow.objects.get(pk=suggested_show_id)
    tvdb_result = tvdb.get_series(s.name)
    description = tvdb_result[0]['overview'] if len(tvdb_result) else ''
    try:
        Show.objects.create(name=s.name, description=description, canonical_name=canonical_format(s.name), auto_erase=(option=='erase'))
    except IntegrityError:
        pass
    s.delete()
    if SuggestedShow.objects.filter(ignored=False).count():
        return HttpResponse(':back')
    else:
        return HttpResponse(':back2')

def ignore_suggested_show(request, suggested_show_id):
    s = SuggestedShow.objects.get(pk=suggested_show_id)
    s.ignored = True
    s.save()
    if SuggestedShow.objects.all().count():
        return HttpResponse(':back')
    else:
        return HttpResponse(':back2')
