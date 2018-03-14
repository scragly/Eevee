# Eevee v2 - In Developement
A Discord helper bot for Pokemon Go communities.

Eevee is a Pokemon Go community manager and coordinator bot for Discord servers, upholding the ideal to respect the Terms of Service of both the game and the associated accounts.

It is written in Python 3.6.1 using the [discord.py v1.0.0a](https://github.com/Rapptz/discord.py/tree/rewrite) library.

This version of Eevee is currently under heavy development and is not recommended for any type of actual usage.

This update aims to meet the following goals:
- [x] Compatible with [discord.py v1.0.0a](https://github.com/Rapptz/discord.py/tree/rewrite)
- [x] Able to be installed as a pip package with dependancies auto-installing
- [x] Redesign Meowth into a modular structure, with extension management
- [x] Ability to update most of the codebase with no downtime or loss of data
- [x] Able to perform all current features of Eevee v1 or excel beyond it

## Proposed Structure:
- Docs
- Readme
- Setup
- Meowth
    - Core
    - Config
    - Data Management
    - Cogs
	    - Server Greeting
	    - Team Management
	    - Wild Tracking
	    - Raid Management
        - Gym Management
