"""Lookout source adapters: calendar, cornerstone, drive delta.

All adapters here are READ-ONLY by design. None of them import or call any
write endpoint on their backing source. The cornerstone wrapper additionally
enforces MC-6 (client_scope required on every read) at the module edge.

Adding a write capability here is an AC-1 / AC-4 violation; do not.
"""
