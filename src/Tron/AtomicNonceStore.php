<?php

declare(strict_types=1);

namespace DeepCore\Tron;

interface AtomicNonceStore
{
    public function issue(string $nonce, string $address, int $expiresAt): void;

    /**
     * Atomically consumes a valid, unused nonce.
     */
    public function consume(string $nonce, string $address, int $now): bool;
}
