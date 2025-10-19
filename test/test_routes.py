import json

from server import get_logged_in_club, loadClubs, set_login

clubs = loadClubs()


def test_index_route(client):
    """Vérifie que la page d'accueil se charge correctement."""
    response = client.get("/")
    assert response.status_code == 200
    assert (
        b"Bienvenue sur le GUDLFT Portal" in response.data
        or b"Welcome to the GUDLFT Portal" in response.data
    )


def test_welcome_route_valid_email(client):
    """Teste la connexion d'un club valide."""
    response = client.post("/welcome", data={"email": "john@simplylift.co"})
    assert response.status_code == 200
    assert b"Bienvenue" in response.data


def test_welcome_route_invalid_email_flash(client):
    """Vérifie qu'un email non enregistré renvoie un message flash et redirige."""
    response = client.post(
        "/welcome", data={"email": "fake@club.com"}, follow_redirects=True
    )
    text = response.data.decode("utf-8")
    assert "Email non autorisé" in text
    assert response.status_code == 200  # redirection vers index


def test_club_route_without_login(client):
    """Vérifie que la route /club redirige si aucun club n'est connecté."""
    response = client.get("/club", follow_redirects=True)
    text = response.data.decode("utf-8")
    assert "Vous devez être connecté" in text


def test_club_route_requires_login(client):
    """Vérifie qu'on ne peut pas accéder à /club sans être connecté."""
    response = client.get("/club", follow_redirects=True)
    assert b"connect" in response.data or response.status_code == 200


def test_set_and_get_login(tmp_path):
    """Teste les fonctions utilitaires de connexion/déconnexion."""
    clubs_data = {"clubs": clubs}
    file = tmp_path / "clubs.json"
    file.write_text(json.dumps(clubs_data))

    # Simuler la connexion
    club = set_login("john@simplylift.co", filepath=file)
    assert club["email"] == "john@simplylift.co"

    # Vérifier que get_logged_in_club renvoie le bon
    logged = get_logged_in_club(filepath=file)
    assert logged["email"] == "john@simplylift.co"


def test_competition_detail_without_login(client):
    """Vérifie que l'accès à la page détail compétition redirige si non connecté."""
    response = client.get("/competition/Competition 1", follow_redirects=True)
    assert b"Vous devez \xc3\xaatre connect\xc3\xa9" in response.data


def test_competition_detail_invalid_name(client, monkeypatch):
    """Vérifie qu'une compétition inexistante redirige avec flash."""
    monkeypatch.setattr(
        "server.get_logged_in_club",
        lambda filepath="clubs.json": {
            "name": "Simply Lift",
            "email": "john@simplylift.co",
            "points": "20",
            "loggin": True,
        },
    )
    response = client.get("/competition/InvalidCompetition", follow_redirects=True)
    assert b"Comp\xc3\xa9tition introuvable" in response.data


def test_purchase_places_success(client, monkeypatch):
    """Teste une réservation de places valide."""
    # Simuler un club connecté
    monkeypatch.setattr(
        "server.get_logged_in_club",
        lambda filepath="clubs.json": {
            "name": "Simply Lift",
            "email": "john@simplylift.co",
            "points": "20",
            "loggin": True,
        },
    )
    monkeypatch.setattr(
        "server.loadClubs",
        lambda: [
            {"name": "Simply Lift", "email": "john@simplylift.co", "points": "20"}
        ],
    )
    monkeypatch.setattr(
        "server.loadCompetitions",
        lambda: [
            {
                "name": "Competition 1",
                "numberOfPlaces": "25",
                "date": "2099-10-20 10:00:00",
            }
        ],
    )

    data = {"competition": "Competition 1", "places": "5"}
    response = client.post("/purchasePlaces", data=data, follow_redirects=True)
    text = response.data.decode("utf-8")
    assert "Réservation réussie" in text


def test_purchase_places_more_than_available(client, monkeypatch):
    """Test réservation de places > places disponibles."""
    monkeypatch.setattr(
        "server.get_logged_in_club",
        lambda filepath="clubs.json": {
            "name": "Simply Lift",
            "email": "john@simplylift.co",
            "points": "20",
            "loggin": True,
        },
    )
    data = {
        "competition": "Competition 1",
        "places": "50",
    }  # suppose 50 > places disponibles
    response = client.post("/purchasePlaces", data=data, follow_redirects=True)
    assert b"demand\xc3\xa9es" in response.data


def test_purchase_places_more_than_points(client, monkeypatch):
    """Test réservation de places > points du club."""
    monkeypatch.setattr(
        "server.get_logged_in_club",
        lambda filepath="clubs.json": {
            "name": "Simply Lift",
            "email": "john@simplylift.co",
            "points": "5",
            "loggin": True,
        },
    )
    data = {"competition": "Competition 1", "places": "10"}  # 10 > 5
    response = client.post("/purchasePlaces", data=data, follow_redirects=True)
    assert b"Pas assez de pts" in response.data


def test_purchase_places_more_than_limit(client, monkeypatch):
    """Test réservation de plus de 12 places."""
    monkeypatch.setattr(
        "server.get_logged_in_club",
        lambda filepath="clubs.json": {
            "name": "Simply Lift",
            "email": "john@simplylift.co",
            "points": "20",
            "loggin": True,
        },
    )
    data = {"competition": "Competition 1", "places": "15"}  # > 12
    response = client.post("/purchasePlaces", data=data, follow_redirects=True)
    assert b"Vous ne pouvez pas r\xc3\xa9server plus de 12 places" in response.data


def test_competition_detail_route(client, monkeypatch):
    """Teste l'accès aux détails d'une compétition."""
    monkeypatch.setattr(
        "server.get_logged_in_club",
        lambda filepath="clubs.json": {
            "name": "Simply Lift",
            "email": "john@simplylift.co",
            "points": "20",
            "loggin": True,
        },
    )

    response = client.get("/competition/Competition 1")
    assert response.status_code == 200
    assert b"Competition" in response.data


def test_logout_redirect(client):
    """Vérifie que /logout redirige bien vers /"""
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"clubs" in response.data
