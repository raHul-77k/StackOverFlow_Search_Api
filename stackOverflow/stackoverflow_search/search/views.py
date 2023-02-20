from django.shortcuts import render
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseBadRequest
import requests
import time

def search(request):
    # Check if user has exceeded search limits
    # Limit to 5 searches per minute and 100 searches per day
    # You can adjust these limits to suit your needs
    user_id = request.session.session_key
    search_count_key = f'search_count_{user_id}'
    minute_count_key = f'minute_count_{user_id}'

    search_count = cache.get(search_count_key, 0)
    minute_count = cache.get(minute_count_key, 0)

    if search_count >= 100:
        return HttpResponseBadRequest('Search limit exceeded. Try again tomorrow.')
    if minute_count >= 5:
        return HttpResponseBadRequest('Search limit exceeded. Try again in a minute.')

    query = request.GET.get('q')
    if not query:
        return render(request, 'search.html')

    # Try to get cached results first
    cached_results = cache.get(query)
    if cached_results:
        questions = cached_results
    else:
        # If not found in cache, make API call and cache the results for 5 minutes
        url = 'https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance&q={}&site=stackoverflow'.format(query)
        response = requests.get(url)
        data = response.json()
        questions = data['items']
        cache.set(query, questions, 300)

    # Increment search counts
    cache.set(search_count_key, search_count + 1, 86400)  # 24 hours
    cache.set(minute_count_key, minute_count + 1, 60)

    # Paginate results
    page = request.GET.get('page', 1)
    paginator = Paginator(questions, 10)
    try:
        questions = paginator.page(page)
    except PageNotAnInteger:
        questions = paginator.page(1)
    except EmptyPage:
        questions = paginator.page(paginator.num_pages)

    context = {
        'questions': questions,
        'query': query
    }

    return render(request, 'search.html', context)