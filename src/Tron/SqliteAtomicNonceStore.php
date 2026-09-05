<?php

declare(strict_types=1);

namespace DeepCore\Tron;

use PDO;

final class SqliteAtomicNonceStore implements AtomicNonceStore
{
    public function __construct(private readonly PDO $pdo)
    {
        $this->pdo->exec(
            'CREATE TABLE IF NOT EXISTS tron_auth_nonces (' .
            'nonce TEXT PRIMARY KEY, ' .
            'address TEXT NOT NULL, ' .
            'expires_at INTEGER NOT NULL, ' .
            'used_at INTEGER NULL)'
        );
    }

    public function issue(string $nonce, string $address, int $expiresAt): void
    {
        $stmt = $this->pdo->prepare(
            'INSERT INTO tron_auth_nonces (nonce, address, expires_at, used_at) '
            . 'VALUES (:nonce, :address, :expires_at, NULL)'
        );

        $stmt->execute([
            ':nonce' => $nonce,
            ':address' => $address,
            ':expires_at' => $expiresAt,
        ]);
    }

    public function consume(string $nonce, string $address, int $now): bool
    {
        $stmt = $this->pdo->prepare(
            'UPDATE tron_auth_nonces '
            . 'SET used_at = :now '
            . 'WHERE nonce = :nonce '
            . 'AND address = :address '
            . 'AND expires_at > :now '
            . 'AND used_at IS NULL'
        );

        $stmt->execute([
            ':now' => $now,
            ':nonce' => $nonce,
            ':address' => $address,
        ]);

        return $stmt->rowCount() === 1;
    }
}
