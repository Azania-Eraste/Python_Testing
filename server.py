import json
import os
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for


def set_login(email, filepath="clubs.json"):
    # Charger le fichier JSON
    with open(filepath, "r") as f:
        data = json.load(f)

    clubs = data.get("clubs", [])

    club_found = None

    for club in clubs:
        if club.get("email") == email:
            club["loggin"] = True
            club_found = club
        else:
            club["loggin"] = False  # tous les autres sont à False

    # Sauvegarder les modifications dans le fichier
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

    return club_found


def get_logged_in_club(filepath="clubs.json"):
    # Charger le fichier JSON
    with open(filepath, "r") as f:
        data = json.load(f)

    clubs = data.get("clubs", [])

    for club in clubs:
        if club.get("loggin") is True:
            return club  # Retourne le club connecté

    return None  # Si aucun club n'est connecté


def loadClubs():
    with open("clubs.json") as c:
        listOfClubs = json.load(c)["clubs"]
        return listOfClubs


def loadCompetitions():
    with open("competitions.json") as comps:
        liste = json.load(comps)["competitions"]
        pastcompetitions = []
        listOfCompetitions = []
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for competition in liste:
            if competition["date"] < today:
                competition["past"] = True
                pastcompetitions.append(competition)
            else:
                competition["past"] = False
                listOfCompetitions.append(competition)
            print(competition)
        for comp in pastcompetitions:
            listOfCompetitions.append(comp)
        return listOfCompetitions


def save_clubs(clubs):
    with open("clubs.json", "w") as f:
        json.dump({"clubs": clubs}, f, indent=4)


def save_competitions(competitions):
    with open("competitions.json", "w") as f:
        json.dump({"competitions": competitions}, f, indent=4)


app = Flask(__name__)
app.secret_key = "something_special"

competitions = loadCompetitions()
clubs = loadClubs()


@app.route("/")
def index():
    clubs = loadClubs()
    return render_template("index.html", clubs=clubs)


@app.route("/welcome", methods=["POST", "GET"])
def welcome():
    email = (
        request.args.get("email")
        if request.method == "GET"
        else request.form.get("email")
    )

    clubs = loadClubs()
    competitions = loadCompetitions()

    club = [club for club in clubs if club["email"] == email]
    if not club:
        flash("Email non autorisé !")
        return redirect(url_for("index"))
    print("club : ", club[0]["name"])
    set_login(email)
    return render_template("welcome.html", club=club, competitions=competitions)


@app.route("/club")
def club():
    clubs = loadClubs()
    club = get_logged_in_club()
    if not club:
        flash("Vous devez être connecté pour voir les clubs.")
        return redirect(url_for("index"))
    return render_template("club.html", clubs=clubs, club=club)


@app.route("/book/<competition>/<club>")
def book(competition, club):
    foundClub = [c for c in clubs if c["name"] == club]
    foundCompetition = [c for c in competitions if c["name"] == competition][0]
    if foundClub and foundCompetition:
        return render_template(
            "booking.html", club=foundClub, competition=foundCompetition
        )
    else:
        flash("Something went wrong-please try again")
        return render_template("welcome.html", club=club, competitions=competitions)


@app.route("/purchasePlaces", methods=["POST"])
def purchasePlaces():
    club_name = get_logged_in_club()["name"]
    comp_name = request.form.get("competition")
    places_requested = int(request.form.get("places"))

    clubs = loadClubs()
    competitions = loadCompetitions()
    print(f"club: {club_name} | competition: {comp_name} | places: {places_requested}")

    # Récupérer le club et la compétition
    club = next((c for c in clubs if c["name"] == club_name), None)
    competition = next((c for c in competitions if c["name"] == comp_name), None)

    if not club or not competition:
        flash("Erreur : Club ou compétition introuvable.")
        return redirect(url_for("index"))

    available_places = int(competition["numberOfPlaces"])
    club_points = int(club["points"])

    # Vérifications Phase 1
    if places_requested > available_places:
        flash(
            f"places : demandées({places_requested}) > disponibles({available_places})!"
        )
    elif places_requested > int(club["points"]):
        flash(f"Pas assez de pts({club['points']}) pour les {places_requested} plcs !")
    elif places_requested > 12:
        flash("Vous ne pouvez pas réserver plus de 12 places par compétition.")
    else:
        # Mise à jour des données
        competition["numberOfPlaces"] = str(available_places - places_requested)
        club["points"] = str(club_points - places_requested)

        save_clubs(clubs)
        save_competitions(competitions)

        flash(f"✅ Réservation réussie : {places_requested} place(s) pour {comp_name}.")

        print(club)
        print(competition)

    return redirect(url_for("welcome", email=club["email"]))


@app.route("/competition/<name>")
def competition_detail(name):
    competitions = loadCompetitions()

    club = get_logged_in_club()
    if not club:
        flash("Vous devez être connecté pour voir les détails de la compétition.")
        return redirect(url_for("index"))
    print("club : ", club)

    competition = next((c for c in competitions if c["name"] == name), None)
    if not competition:
        flash("Compétition introuvable !")
        return redirect(url_for("welcome", email=club["email"] if club else ""))

    return render_template(
        "competition_detail.html", competition=competition, club=club
    )


# TODO: Add route for points display


@app.route("/logout")
def logout():
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
