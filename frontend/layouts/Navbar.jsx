import { Bell, UserCircle } from 'lucide-react';

const Navbar = () => {
  return (
    <header className="flex justify-end items-center p-4 bg-white border-b">
      <div className="flex items-center space-x-4">
        <Bell className="text-gray-600" />
        <UserCircle className="text-gray-600" />
      </div>
    </header>
  );
};

export default Navbar;