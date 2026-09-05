<?php

declare(strict_types=1);

namespace DeepCore\Tron;

final class TronAuthNonceStore
{
    /** @var array<string, array{address:string, expires:int, used:bool}> */
    private array $nonces = [];

    public function issue(string $nonce, string $address, int $expiresAt): void
    {
        $this->nonces[$nonce] = [
            'address' => $address,
            'expires' => $expiresAt,
            'used' => false,
        ];
    }

    public function consume(string $nonce, string $address, int $now): bool
    {
        if (!isset($this->nonces[$nonce])) {
            return false;
        }

        $record = $this->nonces[$nonce];

        if ($record['used'] || $record['address'] !== $address || $now >= $record['expires']) {
            return false;
        }

        $this->nonces[$nonce]['used'] = true;
        return true;
    }
}
