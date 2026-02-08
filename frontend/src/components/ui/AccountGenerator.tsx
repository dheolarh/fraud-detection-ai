import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Lock, Unlock, RefreshCw } from 'lucide-react';

interface AccountGeneratorProps {
    type: 'account' | 'name';
    prefix?: string; // e.g., 'HOV', 'SKY', 'EXT'
    value: string;
    onChange: (value: string) => void;
    label: string;
    disabled?: boolean;
}

// Random name generator
const FIRST_NAMES = [
    'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
    'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
    'Thomas', 'Tchala', 'Sarah', 'Charles', 'Karen', 'Daniel', 'Nancy', 'Matthew', 'Lisa',
    'Sung', 'Tanjiro', 'Eren', 'Levi', 'Lawrence', 'Judith', 'Fisayo', 'Martins', 'Sawyer',
];

const LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Adewale', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas',
    'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White', 'Harris', 'Adenuga', 'Adeniyi',
    'Jin Woo', 'Otoya', 'Amana', 'Gintoki',
];

function generateRandomName(): string {
    const firstName = FIRST_NAMES[Math.floor(Math.random() * FIRST_NAMES.length)];
    const lastName = LAST_NAMES[Math.floor(Math.random() * LAST_NAMES.length)];
    return `${firstName} ${lastName}`;
}

function generateRandomAccount(prefix: string): string {
    // Format: PREFIX-CC-NNNNNN
    // CC = 2 random letters
    // NNNNNN = 6 random digits
    const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const cc = letters[Math.floor(Math.random() * 26)] + letters[Math.floor(Math.random() * 26)];
    const numbers = Math.floor(100000 + Math.random() * 900000); // 6 digits
    return `${prefix}-${cc}-${numbers}`;
}

export function AccountGenerator({
    type,
    prefix = 'ACC',
    value,
    onChange,
    label,
    disabled = false
}: AccountGeneratorProps) {
    const [isLocked, setIsLocked] = useState(false);

    // Load locked state from localStorage
    useEffect(() => {
        const lockKey = `${prefix}_${type}_locked`;
        const savedLockState = localStorage.getItem(lockKey);
        const savedValue = localStorage.getItem(`${prefix}_${type}_value`);

        if (savedLockState === 'true' && savedValue) {
            setIsLocked(true);
            onChange(savedValue);
        } else if (!value) {
            // Auto-generate on mount if no value
            handleGenerate();
        }
    }, []);

    const handleGenerate = () => {
        if (isLocked) return;

        const newValue = type === 'name'
            ? generateRandomName()
            : generateRandomAccount(prefix);

        onChange(newValue);
    };

    const toggleLock = () => {
        const newLockState = !isLocked;
        setIsLocked(newLockState);

        // Save to localStorage
        const lockKey = `${prefix}_${type}_locked`;
        const valueKey = `${prefix}_${type}_value`;

        if (newLockState) {
            localStorage.setItem(lockKey, 'true');
            localStorage.setItem(valueKey, value);
        } else {
            localStorage.removeItem(lockKey);
            localStorage.removeItem(valueKey);
        }
    };

    return (
        <div className="space-y-2">
            <label className="text-sm font-medium">{label}</label>
            <div className="flex gap-2">
                <Input
                    value={value}
                    onChange={(e) => !isLocked && onChange(e.target.value)}
                    readOnly={true}
                    disabled={disabled}
                    className={isLocked ? 'bg-muted/50 cursor-not-allowed' : 'cursor-default'}
                    placeholder={type === 'name' ? 'Generated name' : 'Generated ID'}
                />
                <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={handleGenerate}
                    disabled={isLocked || disabled}
                    title="Generate random"
                >
                    <RefreshCw className="h-4 w-4" />
                </Button>
                <Button
                    type="button"
                    variant={isLocked ? 'default' : 'outline'}
                    size="icon"
                    onClick={toggleLock}
                    disabled={disabled}
                    title={isLocked ? 'Unlock' : 'Lock'}
                >
                    {isLocked ? <Lock className="h-4 w-4" /> : <Unlock className="h-4 w-4" />}
                </Button>
            </div>
            {isLocked && (
                <p className="text-xs text-muted-foreground">
                    Locked - This value will persist across sessions
                </p>
            )}
        </div>
    );
}
