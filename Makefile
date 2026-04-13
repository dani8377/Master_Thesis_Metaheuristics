UV      := uv run --with numpy --with pandas --with matplotlib python
EV_DIR  := EV_routing
CS_DIR  := Cloud scheduling

.PHONY: all ev cloud

all: ev cloud

ev:
	cd "$(EV_DIR)" && $(UV) main.py

cloud:
	cd "$(CS_DIR)" && $(UV) main.py
