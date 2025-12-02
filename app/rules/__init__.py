"""Species rules package."""
from .seasonality import get_running_factor, is_species_running, SPECIES_LIST
from .bite_logic import calculate_bite_score, get_bite_label

__all__ = [
    'get_running_factor',
    'is_species_running',
    'SPECIES_LIST',
    'calculate_bite_score',
    'get_bite_label'
]
