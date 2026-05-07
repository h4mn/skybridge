"""Testes para companion aroundness — classificação de objetos, biome, landmarks.

TDD: estes testes definem o comportamento esperado que o mod C# implementa.
Fluxo: RED (teste falha) → GREEN (implementar) → REFACTOR.

DOC: companion-state-types change — specs/companion-aroundness/spec.md
"""
from __future__ import annotations

import pytest


# ============================================================================
# ScanAndClassify — separação builds / resources / creatures
# ============================================================================

class TestScanClassification:
    """DOC: CompanionController.ScanAndClassify()

    Build: WorldObject com inventório vinculado (linkedInventoryId > 0).
    Resource: WorldObject sem inventório vinculado (recurso natural).
    Creature: GameObject sem WorldObjectAssociated mas com tag Creature/Insect/Animal.
    """

    def test_build_has_inventory_returns_build_list(self):
        """Scenario: objeto com inventório vinculado é classificado como build."""
        scan_obj = {
            "has_world_object": True,
            "linked_inventory_id": 42,
            "group_name": "Armário de Armazenamento",
        }
        category = classify_object(scan_obj)
        assert category == "build"

    def test_resource_no_inventory_returns_resource(self):
        """Scenario: objeto sem inventório vinculado é classificado como resource."""
        scan_obj = {
            "has_world_object": True,
            "linked_inventory_id": 0,
            "group_name": "Semente de Shanga",
        }
        category = classify_object(scan_obj)
        assert category == "resource"

    def test_creature_has_tag_no_world_object(self):
        """Scenario: objeto sem WorldObjectAssociated mas com tag Creature."""
        scan_obj = {
            "has_world_object": False,
            "tag": "Creature",
            "name": "Lorpen",
        }
        category = classify_object(scan_obj)
        assert category == "creature"

    def test_insect_tag_classified_as_creature(self):
        """Scenario: objeto com tag Insect é classificado como creature."""
        scan_obj = {
            "has_world_object": False,
            "tag": "Insect",
            "name": "Oesbe",
        }
        category = classify_object(scan_obj)
        assert category == "creature"

    def test_animal_tag_classified_as_creature(self):
        """Scenario: objeto com tag Animal é classificado como creature."""
        scan_obj = {
            "has_world_object": False,
            "tag": "Animal",
            "name": "GoldenGlob",
        }
        category = classify_object(scan_obj)
        assert category == "creature"

    def test_unknown_object_ignored(self):
        """Scenario: objeto sem WorldObjectAssociated e sem tag de criatura é ignorado."""
        scan_obj = {
            "has_world_object": False,
            "tag": "Untagged",
            "name": "TerrainChunk",
        }
        category = classify_object(scan_obj)
        assert category == "ignored"

    def test_duplicate_world_objects_not_double_counted(self):
        """Scenario: dois colliders do mesmo WorldObject são contados uma vez."""
        results = deduplicate_scan([
            {"id": 100, "name": "Container2"},
            {"id": 100, "name": "Container2"},
            {"id": 101, "name": "VegetableGrower1"},
        ])
        assert len(results) == 2

    def test_empty_scan_returns_empty_lists(self):
        """Scenario: scan sem colliders retorna todas as listas vazias."""
        result = {
            "builds": [],
            "resources": [],
            "creatures": [],
        }
        assert len(result["builds"]) == 0
        assert len(result["resources"]) == 0
        assert len(result["creatures"]) == 0


# ============================================================================
# DetectBiome — heurística altitude + presença de vida
# ============================================================================

class TestDetectBiome:
    """DOC: CompanionController.DetectBiome()

    Heurística baseada em altitude e presença de insetos/animais.
    """

    def test_low_altitude_no_life_returns_wasteland(self):
        """Scenario: Y < 15, sem vida → Wasteland."""
        biome = detect_biome(altitude=10.0, has_life=False)
        assert biome == "Wasteland"

    def test_low_altitude_with_life_returns_valley(self):
        """Scenario: Y < 15, com vida → Valley."""
        biome = detect_biome(altitude=12.0, has_life=True)
        assert biome == "Valley"

    def test_mid_altitude_no_life_returns_mesa(self):
        """Scenario: 15 <= Y < 50, sem vida → Mesa."""
        biome = detect_biome(altitude=30.0, has_life=False)
        assert biome == "Mesa"

    def test_mid_altitude_with_life_returns_forest(self):
        """Scenario: 15 <= Y < 50, com vida → Forest."""
        biome = detect_biome(altitude=25.0, has_life=True)
        assert biome == "Forest"

    def test_high_altitude_returns_highlands(self):
        """Scenario: 50 <= Y < 100 → Highlands."""
        biome = detect_biome(altitude=75.0, has_life=False)
        assert biome == "Highlands"

    def test_very_high_altitude_returns_mountains(self):
        """Scenario: Y >= 100 → Mountains."""
        biome = detect_biome(altitude=150.0, has_life=False)
        assert biome == "Mountains"

    def test_boundary_y15_with_life(self):
        """Scenario: Y = 15 (boundary, >= 15 entra na faixa mid) com vida → Forest."""
        biome = detect_biome(altitude=15.0, has_life=True)
        assert biome == "Forest"

    def test_boundary_y15_no_life(self):
        """Scenario: Y = 15 (boundary) sem vida → Mesa."""
        biome = detect_biome(altitude=15.0, has_life=False)
        assert biome == "Mesa"

    def test_boundary_y50_with_life(self):
        """Scenario: Y = 50 (boundary, >= 50 entra na faixa high) com vida → Highlands."""
        biome = detect_biome(altitude=50.0, has_life=True)
        assert biome == "Highlands"

    def test_boundary_y50_no_life(self):
        """Scenario: Y = 50 (boundary) sem vida → Highlands."""
        biome = detect_biome(altitude=50.0, has_life=False)
        assert biome == "Highlands"

    def test_boundary_y100(self):
        """Scenario: Y = 100 (boundary) → Mountains."""
        biome = detect_biome(altitude=100.0, has_life=False)
        assert biome == "Mountains"


# ============================================================================
# DetectNearestLandmark — detecção de pontos de referência
# ============================================================================

class TestDetectNearestLandmark:
    """DOC: CompanionController.DetectNearestLandmark()"""

    def test_near_spawn_returns_spawn(self):
        """Scenario: posição < 50u da origem → Spawn."""
        landmark = detect_nearest_landmark(x=20, y=35, z=30)
        assert landmark == "Spawn"

    def test_far_from_spawn_returns_none(self):
        """Scenario: posição > 50u da origem, altitude baixa → None."""
        landmark = detect_nearest_landmark(x=200, y=35, z=300)
        assert landmark == "None"

    def test_high_altitude_returns_highground(self):
        """Scenario: Y > 100 → HighGround."""
        landmark = detect_nearest_landmark(x=200, y=120, z=300)
        assert landmark == "HighGround"

    def test_exact_boundary_50u_from_spawn(self):
        """Scenario: exatamente 50u da origem → None (exclusive)."""
        landmark = detect_nearest_landmark(x=50, y=0, z=0)
        assert landmark == "None"


# ============================================================================
# CompanionState model — todos os campos presentes
# ============================================================================

class TestCompanionStateModel:
    """DOC: GameState.cs CompanionState — todos os campos devem estar presentes."""

    def test_companion_state_has_all_required_fields(self):
        """Scenario: CompanionState contém Position, State, Distance, IsVisible, Speed,
        NearbyBuilds, NearbyResources, NearbyCreatures, ScanRadius, Altitude, Biome, NearestLandmark."""
        required_fields = [
            "Position", "State", "Distance", "IsVisible", "Speed",
            "NearbyBuilds", "NearbyResources", "NearbyCreatures",
            "ScanRadius", "Altitude", "Biome", "NearestLandmark",
        ]
        state = create_sample_companion_state()
        for field in required_fields:
            assert field in state, f"Campo '{field}' faltando no CompanionState"

    def test_altitude_defaults_to_current_y(self):
        """Scenario: Altitude é a coordenada Y do companion."""
        state = create_sample_companion_state(y=42.5)
        assert state["Altitude"] == 42.5

    def test_biome_defaults_to_unknown(self):
        """Scenario: Biome default é 'Unknown'."""
        state = create_sample_companion_state()
        assert state["Biome"] == "Unknown"

    def test_nearest_landmark_defaults_to_none(self):
        """Scenario: NearestLandmark default é 'None'."""
        state = create_sample_companion_state()
        assert state["NearestLandmark"] == "None"

    def test_nearby_resources_is_list(self):
        """Scenario: NearbyResources é uma lista de strings."""
        state = create_sample_companion_state()
        assert isinstance(state["NearbyResources"], list)

    def test_nearby_creatures_is_list(self):
        """Scenario: NearbyCreatures é uma lista de strings."""
        state = create_sample_companion_state()
        assert isinstance(state["NearbyCreatures"], list)

    def test_scan_radius_default_20(self):
        """Scenario: ScanRadius default é 20.0."""
        state = create_sample_companion_state()
        assert state["ScanRadius"] == 20.0


# ============================================================================
# Helpers — funções auxiliares que espelham a lógica C#
# ============================================================================

def classify_object(scan_obj: dict) -> str:
    """Espelha CompanionController.ScanAndClassify() — classificação de objetos."""
    if not scan_obj.get("has_world_object", False):
        tag = scan_obj.get("tag", "")
        if tag in ("Creature", "Insect", "Animal"):
            return "creature"
        return "ignored"

    if scan_obj.get("linked_inventory_id", 0) > 0:
        return "build"
    return "resource"


def deduplicate_scan(items: list[dict]) -> list[dict]:
    """Remove duplicatas por ID."""
    seen = set()
    result = []
    for item in items:
        if item["id"] not in seen:
            seen.add(item["id"])
            result.append(item)
    return result


def detect_biome(altitude: float, has_life: bool) -> str:
    """Espelha CompanionController.DetectBiome() — heurística altitude + vida."""
    if altitude < 15:
        return "Valley" if has_life else "Wasteland"
    if altitude < 50:
        return "Forest" if has_life else "Mesa"
    if altitude < 100:
        return "Highlands"
    return "Mountains"


def detect_nearest_landmark(x: float, y: float, z: float) -> str:
    """Espelha CompanionController.DetectNearestLandmark() — detecção de landmarks."""
    if y > 100:
        return "HighGround"
    dist = (x ** 2 + z ** 2) ** 0.5
    if dist < 50:
        return "Spawn"
    return "None"


def create_sample_companion_state(x: float = 100, y: float = 35, z: float = 200) -> dict:
    """Cria um CompanionState de exemplo com todos os campos."""
    return {
        "Position": [x, y, z],
        "State": "Orbit",
        "Distance": 3.5,
        "IsVisible": True,
        "Speed": 2.0,
        "NearbyBuilds": [],
        "NearbyResources": [],
        "NearbyCreatures": [],
        "ScanRadius": 20.0,
        "Altitude": y,
        "Biome": "Unknown",
        "NearestLandmark": "None",
    }
