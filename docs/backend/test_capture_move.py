#!/usr/bin/env python
"""
Test script to verify capture moves work in checkers competitive.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/var/www/html/rumo_rush/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings')
django.setup()

from apps.games.game_logic.checkers_competitive import CheckersBoard, Color, Position, Move, CheckersPiece, PieceType, convert_board_to_unicode

def test_capture_move():
    print("=" * 80)
    print("Testing Checkers Competitive - Capture Move")
    print("=" * 80)
    
    # Create a board with a simple capture scenario
    board = CheckersBoard()
    
    # Clear the board first
    for row in range(10):
        for col in range(10):
            board.set_piece(Position(row, col), None)
    
    # Setup a simple capture scenario:
    # BLACK piece at (4, 1) - can move DOWN
    # RED piece at (5, 2) <- to be captured  
    # Empty at (6, 3) <- landing position
    
    board.set_piece(Position(4, 1), CheckersPiece(PieceType.MAN, Color.BLACK))
    board.set_piece(Position(5, 2), CheckersPiece(PieceType.MAN, Color.RED))
    # (6, 3) is already empty
    
    # Set current player to BLACK (since BLACK piece is at (4,1))
    board.current_player = Color.BLACK
    
    # Start the timer
    board.timer.start_move(Color.BLACK)
    
    print("\n📊 Initial Board State:")
    game_state = board.to_dict()
    print(convert_board_to_unicode(game_state))
    
    print(f"\n🎮 Current player: {board.current_player.value}")
    print(f"🎯 Piece at (4,1): {board.get_piece(Position(4,1))}")
    print(f"🎯 Piece at (5,2): {board.get_piece(Position(5,2))}")
    print(f"🎯 Piece at (6,3): {board.get_piece(Position(6,3))}")
    
    # Get possible moves for the BLACK piece
    print("\n🔍 Getting possible moves for BLACK piece at (4,1)...")
    possible_moves = board.get_possible_moves(Position(4, 1))
    
    print(f"✅ Found {len(possible_moves)} possible moves:")
    for i, move in enumerate(possible_moves):
        print(f"  {i+1}. From {move.from_pos} to {move.to_pos}, captures: {move.captured_pieces}, points: {move.points_earned}")
    
    if not possible_moves:
        print("❌ No possible moves found!")
        return False
    
    # Try to execute the first move (should be the capture)
    move_to_execute = possible_moves[0]
    print(f"\n🎯 Executing move: {move_to_execute.from_pos} -> {move_to_execute.to_pos}")
    
    success = board.make_move(move_to_execute)
    
    if success:
        print("✅ Move executed successfully!")
        print("\n📊 Board after move:")
        game_state_after = board.to_dict()
        print(convert_board_to_unicode(game_state_after))
        print(f"\n🏆 Scores:")
        print(f"  RED: {board.red_score.points} points")
        print(f"  BLACK: {board.black_score.points} points")
        return True
    else:
        print("❌ Move execution failed!")
        return False

if __name__ == '__main__':
    success = test_capture_move()
    sys.exit(0 if success else 1)
