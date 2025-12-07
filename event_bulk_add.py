"""
Minimal bulk poster: log in and POST events (no verification).

Usage:
  pip install requests
  python event_bulk_add.py
"""

import os
import requests

BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
IDENTIFIANT = 'admin@admin.com'
MDP = 'admin@admin.com'

EVENTS = [
    # January 2026 - 10 events
    {"title": "Atelier d'observation des oiseaux", "start": "2026-01-03T09:30", "end": "2026-01-03T11:30", "description": "Matinée d'initiation à l'ornithologie pour petits et grands."},
    {"title": "Visite guidée: mammifères nocturnes", "start": "2026-01-05T18:00", "end": "2026-01-05T20:00", "description": "Découverte des espèces actives la nuit."},
    {"title": "Rencontre avec les soigneurs - primates", "start": "2026-01-07T14:00", "end": "2026-01-07T15:00", "description": "Questions/réponses et démonstrations autour des primates."},
    {"title": "Atelier famille: traces et empreintes", "start": "2026-01-10T10:00", "end": "2026-01-10T12:00", "description": "Apprenez à identifier les traces des animaux."},
    {"title": "Exposition photos: Faune d'hiver (vernissage)", "start": "2026-01-12T17:00", "end": "2026-01-12T19:00", "description": "Vernissage de l'exposition de photos."},
    {"title": "Atelier soins: alimentation des oiseaux", "start": "2026-01-15T10:00", "end": "2026-01-15T11:30", "description": "Démonstration sur l'alimentation adaptée des oiseaux en hiver."},
    {"title": "Week-end famille: jeux et animations", "start": "2026-01-17T10:00", "end": "2026-01-18T17:00", "description": "Ateliers créatifs, parcours découverte et visites guidées pour familles."},
    {"title": "Conférence: migrations animales", "start": "2026-01-20T14:00", "end": "2026-01-20T16:00", "description": "Présentation par un spécialiste des migrations."},
    {"title": "Formation: premiers secours animaliers", "start": "2026-01-24T09:00", "end": "2026-01-24T16:00", "description": "Journée de formation pour bénévoles et étudiants vétérinaires."},
    {"title": "Soirée astronomie et animaux", "start": "2026-01-29T20:00", "end": "2026-01-29T22:30", "description": "Observation du ciel et liens entre comportement animal et nuit."},

    # February 2026 - 10 events
    {"title": "Festival des papillons (serre éducative)", "start": "2026-02-02T09:00", "end": "2026-02-06T18:00", "description": "Cinq jours dédiés aux papillons et à leur habitat."},
    {"title": "Visite guidée: coulisses de l'aquarium", "start": "2026-02-08T11:00", "end": "2026-02-08T12:30", "description": "Visite commentée des installations aquatiques et des soins."},
    {"title": "Atelier enfants: peinture animale", "start": "2026-02-10T10:00", "end": "2026-02-10T12:00", "description": "Atelier créatif pour les plus jeunes."},
    {"title": "Soirée contes et animaux", "start": "2026-02-12T18:30", "end": "2026-02-12T20:00", "description": "Lectures et contes autour des animaux pour toute la famille."},
    {"title": "Saint-Valentin: promenade romantique au zoo", "start": "2026-02-14T18:00", "end": "2026-02-14T21:00", "description": "Soirée spéciale avec éclairage, musique et petit buffet (places limitées)."},
    {"title": "Journée biodiversité: conférences", "start": "2026-02-16T09:30", "end": "2026-02-16T17:00", "description": "Conférences et tables rondes avec intervenants spécialisés."},
    {"title": "Visite thématique: animaux polaires", "start": "2026-02-18T11:00", "end": "2026-02-18T13:00", "description": "Présentation des adaptations des espèces polaires."},
    {"title": "Atelier scientifique: laboratoire mobile", "start": "2026-02-20T10:00", "end": "2026-02-20T12:30", "description": "Expériences et démonstrations scientifiques pour enfants."},
    {"title": "Weekend solidarité: collecte pour la faune", "start": "2026-02-22T09:00", "end": "2026-02-23T17:00", "description": "Collecte de matériel et dons au profit de programmes de réhabilitation."},
    {"title": "Atelier hivernal: constructions pour animaux", "start": "2026-02-26T10:00", "end": "2026-02-26T13:00", "description": "Atelier participatif pour fabriquer abris et nichoirs."}
]


def main():
    s = requests.Session()
    login_url = BASE_URL.rstrip('/') + '/login'
    add_url = BASE_URL.rstrip('/') + '/addevent'

    # login
    s.post(login_url, data={'identifiant': IDENTIFIANT, 'mdp': MDP})

    # post events
    for ev in EVENTS:
        resp = s.post(add_url, data={'title': ev['title'], 'start': ev['start'], 'end': ev['end'], 'description': ev.get('description', '')})
        print(f"POST {ev['title']} -> status {resp.status_code}")


if __name__ == '__main__':
    main()
