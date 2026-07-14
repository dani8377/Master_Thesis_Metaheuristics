UV      := uv run --with numpy --with pandas --with matplotlib --with pyyaml --with scipy python
EV_DIR  := EV_routing
CS_DIR  := Cloud_scheduling

.PHONY: all ev cloud

all: ev cloud

ev:
	PYTHONPATH=$(EV_DIR) $(UV) $(EV_DIR)/main.py

cloud:
	cd "$(CS_DIR)" && $(UV) main.py
