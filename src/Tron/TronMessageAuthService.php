<?php

declare(strict_types=1);

namespace DeepCore\Tron;

use IEXBase\TronAPI\Crypto\MessageSigner;
use RuntimeException;

final class TronMessageAuthService
{
    public function __construct(private readonly TronAuthNonceStore $nonceStore)
    {
    }

    public function verify(
        TronAuthChallenge $challenge,
        string $signatureHex,
        int $now,
    ): void {
        if ($now >= $challenge->expiresAt->getTimestamp()) {
            throw new RuntimeException('TRON_AUTH_CHALLENGE_EXPIRED');
        }

        $valid = MessageSigner::verify(
            $challenge->canonicalMessage(),
            $signatureHex,
            $challenge->address,
        );

        if (!$valid) {
            throw new RuntimeException('TRON_MESSAGE_SIGNATURE_INVALID');
        }

        if (!$this->nonceStore->consume($challenge->nonce, $challenge->address, $now)) {
            throw new RuntimeException('TRON_AUTH_NONCE_INVALID_OR_REPLAYED');
        }
    }
}
