"""
startup.py - Application Startup Configuration Module

This module handles the configuration of application startup behavior,
including registry key management for automatic startup functionality.

@author Abdullah
@version 1.0
@since 2024
"""

# Use a more unique registry key

def startup():
    """
    Configures the application startup registry key.
    
    This function defines the registry path used for managing the application's
    automatic startup behavior in Windows.
    
    @returns {str} Registry path for startup configuration
    """
    RUN_PATH = "HKEY_CURRENT_USER\\Software\\ItHoly\\PordaAI\\Run"
    return RUN_PATH
    