"""
data_structures.py - Core data structures
Core data structures including diagonal bitmap.
Capable of O(1) diagonal conflict detection.
"""

class DiagonalBitmap:
    """Diagonal bitmap - O(1) diagonal crossing conflict detection"""
    
    def __init__(self):
        self.cells = {}
    
    def _get_cell_and_type(self, x1, y1, x2, y2):
        """Get the cell and type of the diagonal"""
        dx = x2 - x1
        dy = y2 - y1
        
        if abs(dx) != 1 or abs(dy) != 1:
            return None
        
        cell_x = min(x1, x2)
        cell_y = min(y1, y2)
        
        if dx * dy > 0:
            diag_type = 'main'
        else:
            diag_type = 'anti'
        
        return (cell_x, cell_y, diag_type)
    
    def add_diagonal(self, x1, y1, x2, y2, net_id):
        """Add diagonal"""
        result = self._get_cell_and_type(x1, y1, x2, y2)
        if result is None:
            return False
        
        cell_x, cell_y, diag_type = result
        cell_key = (cell_x, cell_y)
        
        if cell_key not in self.cells:
            self.cells[cell_key] = {}
        
        self.cells[cell_key][diag_type] = net_id
        return True
    
    def check_conflict(self, x1, y1, x2, y2, net_id):
        """Check diagonal conflict"""
        result = self._get_cell_and_type(x1, y1, x2, y2)
        if result is None:
            return False
        
        cell_x, cell_y, diag_type = result
        cell_key = (cell_x, cell_y)
        
        if cell_key not in self.cells:
            return False
        
        cell_data = self.cells[cell_key]
        opposite_type = 'anti' if diag_type == 'main' else 'main'
        
        if opposite_type in cell_data:
            existing_net_id = cell_data[opposite_type]
            if existing_net_id != net_id:
                return True
        
        return False
    
    def remove_net(self, net_id):
        """Remove all diagonals of specified network"""
        cells_to_clean = []
        for cell_key, cell_data in self.cells.items():
            keys_to_remove = [k for k, v in cell_data.items() if v == net_id]
            for k in keys_to_remove:
                del cell_data[k]
            if not cell_data:
                cells_to_clean.append(cell_key)
        
        for cell_key in cells_to_clean:
            del self.cells[cell_key]
    
    def clear(self):
        """Clear all data"""
        self.cells.clear()
    
    def copy(self):
        """Deep copy"""
        new_bitmap = DiagonalBitmap()
        new_bitmap.cells = {k: dict(v) for k, v in self.cells.items()}
        return new_bitmap
